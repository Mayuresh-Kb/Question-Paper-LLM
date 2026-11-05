import copy
import io
import json
import time
from uuid import uuid4
import fitz
import httpx
import pytest
from fastapi.testclient import TestClient
from app.core import config
from app.core.utils import cleanup_expired
from main import create_app


def generate(client,payload,token):
    response=client.post('/generate',json=payload,headers=token)
    assert response.status_code==200,response.text
    return response.json()


def test_upload_generate_download_and_reload(client,upload,token,payload):
    assert client.get('/health').json()['gemini_configured'] is False
    assert client.get(f"/uploads/{upload['upload_id']}",headers=token).json()['units']==upload['units']
    result=generate(client,payload,token)
    pdf=client.get(result['download_url'],headers=token)
    assert pdf.status_code==200
    assert pdf.content.startswith(b'%PDF')
    with fitz.open(stream=pdf.content,filetype='pdf') as doc:
        text='\n'.join(p.get_text() for p in doc)
        assert 'Total marks: 15' in text
        assert 'College <Engineering> & Science' in text
        assert 'Use a < b' in text
        assert 'OR' in text
        assert 'Page 1' in text
    assert client.get(f"/papers/{result['pdf_id']}",headers=token).json()['paper']['total_marks']==15


def test_session_access_required(client,upload,token,payload):
    result=generate(client,payload,token)
    for endpoint in [f"/uploads/{upload['upload_id']}",f"/papers/{result['pdf_id']}",result['download_url']]:
        assert client.get(endpoint,headers={'X-Session-Token':'wrong'}).status_code==403
        assert client.get(endpoint).status_code==(403 if endpoint.startswith('/download/') else 422)
    assert client.post('/generate',json=payload,headers={'X-Session-Token':'wrong'}).status_code==403


def test_uuid_validation_prevents_wildcards(client,token,payload):
    payload['upload_id']='*'
    assert client.post('/generate',json=payload,headers=token).status_code==422
    assert client.get('/download/not-a-uuid',headers=token).status_code==422


def test_invalid_totals_and_missing_units(client,token,payload):
    payload['total_marks']=100
    assert client.post('/generate',json=payload,headers=token).status_code==422
    payload['total_marks']=15;payload['units'][0]['unit_id']=str(uuid4())
    assert client.post('/generate',json=payload,headers=token).status_code==400


def test_duplicate_filenames_preserve_upload_order(client,bank_text):
    response=client.post('/upload',files=[('files',('same.txt',bank_text.encode())),('files',('same.txt',bank_text.replace('concept','graph').encode()))])
    assert response.status_code==200,response.text
    units=response.json()['units']
    assert len(units)==2 and units[0]['id']!=units[1]['id']
    assert 'concept' in units[0]['questions'][0]['text']
    assert 'graph' in units[1]['questions'][0]['text']


def test_unequal_marks_and_subset_selection(client,bank_text):
    data=client.post('/upload',files=[('files',('z.txt',bank_text.encode())),('files',('a.txt',bank_text.replace('concept','graph').encode()))]).json()
    headers={'X-Session-Token':data['session_token']}
    payload={'upload_id':data['upload_id'],'total_marks':35,'units':[{'unit_id':u['id'],'marks':m} for u,m in zip(data['units'],[15,20])]}
    result=generate(client,payload,headers)
    assert [u['marks'] for u in result['paper']['units']]==[15,20]
    payload['units']=payload['units'][1:];payload['total_marks']=20
    assert len(generate(client,payload,headers)['paper']['units'])==1


def test_upload_failure_rolls_back(client,bank_text):
    before=set(config.UPLOAD_DIR.iterdir())
    r=client.post('/upload',files=[('files',('good.txt',bank_text.encode())),('files',('bad.doc',b'bad'))])
    assert r.status_code==400
    assert set(config.UPLOAD_DIR.iterdir())==before


def test_corrupt_pdf_rejected(client):
    assert client.post('/upload',files=[('files',('bad.pdf',b'not a pdf'))]).status_code==400


def test_upload_size_limited(client,monkeypatch):
    monkeypatch.setattr(config,'MAX_FILE_BYTES',20)
    assert client.post('/upload',files=[('files',('big.txt',b'x'*30))]).status_code==413


def test_bank_review_persists_and_forbids_injected_paths(client,upload,token):
    unit=upload['units'][0]
    keys=['id','text','source_marks','bloom','topic','enabled','include_figures']
    payload={'unit_id':unit['id'],'name':'Reviewed unit','questions':[{k:q[k] for k in keys} for q in unit['questions']]}
    payload['questions'][0]['text']='Explain a corrected question about trees.'
    response=client.put(f"/uploads/{upload['upload_id']}/unit",json=payload,headers=token)
    assert response.status_code==200,response.text
    assert response.json()['units'][0]['name']=='Reviewed unit'
    payload['questions'][0]['assets']=['/etc/passwd']
    assert client.put(f"/uploads/{upload['upload_id']}/unit",json=payload,headers=token).status_code==422


def test_bank_review_rejects_enabled_gibberish(client,upload,token):
    unit=upload['units'][0]
    keys=['id','text','source_marks','bloom','topic','enabled','include_figures']
    payload={'unit_id':unit['id'],'name':unit['name'],'questions':[{k:q[k] for k in keys} for q in unit['questions']]}
    payload['questions'][0]['text']='||||||||||||||||'
    response=client.put(f"/uploads/{upload['upload_id']}/unit",json=payload,headers=token)
    assert response.status_code==400
    assert 'needs correction' in response.json()['detail']


def test_replace_creates_new_paper_and_preserves_marks(client,upload,token,payload):
    result=generate(client,payload,token)
    qs=[q for a in result['paper']['units'][0]['alternatives'] for q in a['questions']]
    used={q['id'] for q in qs}
    spare=next(q for q in upload['units'][0]['questions'] if q['id'] not in used)
    response=client.post(f"/papers/{result['pdf_id']}/replace",json={'question_id':qs[0]['id'],'replacement_id':spare['id']},headers=token)
    assert response.status_code==200,response.text
    assert response.json()['pdf_id']!=result['pdf_id']
    new=response.json()['paper']['units'][0]['alternatives'][0]['questions'][0]
    assert new['id']==spare['id'] and new['marks']==qs[0]['marks']
    duplicate=client.post(f"/papers/{result['pdf_id']}/replace",json={'question_id':qs[0]['id'],'replacement_id':qs[1]['id']},headers=token)
    assert duplicate.status_code==400


def test_gemini_unconfigured_and_insufficient_bank(client,payload,token):
    payload['mode']='gemini'
    r=client.post('/generate',json=payload,headers=token)
    assert r.status_code==503 and 'not configured' in r.json()['detail']
    payload['units'][0]['questions_per_alternative']=7
    r=client.post('/generate',json=payload,headers=token)
    assert r.status_code==400 and '14 unique' in r.json()['detail']


def test_mocked_gemini_validates_ids_and_renders(client,upload,token,payload,monkeypatch):
    monkeypatch.setattr(config,'GEMINI_API_KEY','test-not-a-real-key')
    ids=[q['id'] for q in upload['units'][0]['questions']]
    def post(self,url,**kwargs):
        assert kwargs['headers']['x-goog-api-key']=='test-not-a-real-key'
        body={'units':[{'unit_id':upload['units'][0]['id'],'alternatives':[ids[:2],ids[2:4]]}]}
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(body)}]}}]})
    monkeypatch.setattr(httpx.Client,'post',post)
    # Use the provider directly; the TestClient also uses httpx.Client.post.
    from app.schemas.models import GenerateRequest
    from app.services.llm_service import build_paper
    payload['mode']='gemini'
    paper=build_paper(GenerateRequest.model_validate(payload),upload)
    assert paper['provider']=='Gemini'
    assert paper['units'][0]['alternatives'][0]['questions'][0]['id']==ids[0]


def test_expiry_and_cleanup_preserve_nonmanaged_files(client,upload,token):
    manifest=config.UPLOAD_DIR/upload['upload_id']/'manifest.json'
    data=json.loads(manifest.read_text());data['expires_at']=time.time()-1;manifest.write_text(json.dumps(data))
    assert client.get(f"/uploads/{upload['upload_id']}",headers=token).status_code==410
    sample=config.UPLOAD_DIR/'keep.txt';sample.write_text('keep')
    cleanup_expired()
    assert not manifest.exists()
    assert sample.exists()


def test_cors_preflight(client):
    response=client.options('/generate',headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type,x-session-token'})
    assert response.status_code==200
    assert response.headers['access-control-allow-origin']=='http://localhost:5173'


def test_production_app_serves_spa_assets_and_prefixed_api(tmp_path,monkeypatch):
    static=tmp_path/'static'
    assets=static/'assets'
    assets.mkdir(parents=True)
    (static/'index.html').write_text('<!doctype html><title>Question Paper</title>')
    (assets/'app.js').write_text('window.questionPaper=true')
    monkeypatch.setattr(config,'UPLOAD_DIR',tmp_path/'sessions')
    monkeypatch.setattr(config,'OUT_DIR',tmp_path/'papers')

    with TestClient(create_app(static)) as production:
        assert production.get('/api/health').status_code==200
        assert production.get('/').text.startswith('<!doctype html>')
        assert production.get('/upload').text.startswith('<!doctype html>')
        asset=production.get('/assets/app.js')
        assert asset.text=='window.questionPaper=true'
        assert asset.headers['cache-control']=='public, max-age=31536000, immutable'
        assert production.get('/api/does-not-exist').status_code==404


def test_protected_preview_and_expiring_download_link(client,token,payload):
    result=generate(client,payload,token)
    base=f"/papers/{result['pdf_id']}"
    assert client.get(base,headers=token).json()['page_count']>=1
    page=client.get(base+'/pages/1',headers=token)
    assert page.status_code==200 and page.content.startswith(b'\x89PNG')
    assert client.get(base+'/pages/0',headers=token).status_code==404
    assert client.get(base+'/pages/1',headers={'X-Session-Token':'wrong'}).status_code==403
    signed=client.get(base+'/download-link',headers=token).json()['url']
    assert client.get(signed).content.startswith(b'%PDF')
    assert client.get(signed+'0').status_code==403
    from urllib.parse import urlparse,parse_qs
    parsed=parse_qs(urlparse(signed).query)
    expired=f"/download/{result['pdf_id']}?expires=1&signature={parsed['signature'][0]}"
    assert client.get(expired).status_code==403
    foreign=signed.replace(result['pdf_id'],str(uuid4()))
    assert client.get(foreign).status_code==404


def test_figures_survive_the_entire_pdf_pipeline(client):
    with fitz.open() as source:
        page=source.new_page()
        for index,y in enumerate([60,190,290,390]):
            page.insert_text((50,y),f'{index+1}. Explain the properties of system {index+1}. [5 Marks] [BTL: 2]')
        page.draw_rect(fitz.Rect(70,95,200,145),color=(0,0,0))
        page.insert_text((90,120),'Source system')
        raw=source.tobytes()
    response=client.post('/upload',files=[('files',('with-figure.pdf',raw,'application/pdf'))])
    assert response.status_code==200,response.text
    upload=response.json();token={'X-Session-Token':upload['session_token']};unit=upload['units'][0]
    figure=unit['questions'][0]['assets'][0]
    asset=f"/uploads/{upload['upload_id']}/assets/{figure.removesuffix('.png')}"
    assert client.get(asset,headers=token).content.startswith(b'\x89PNG')
    assert client.get(asset,headers={'X-Session-Token':'wrong'}).status_code==403
    result=generate(client,{'upload_id':upload['upload_id'],'total_marks':10,'units':[{'unit_id':unit['id'],'marks':10,'questions_per_alternative':2}]},token)
    with fitz.open(stream=client.get(result['download_url'],headers=token).content,filetype='pdf') as pdf:
        assert sum(len(page.get_images()) for page in pdf)>=1
