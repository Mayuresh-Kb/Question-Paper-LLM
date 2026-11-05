from uuid import uuid4
import pytest
from pydantic import ValidationError
from app.schemas.models import GenerateRequest
from app.services.llm_service import allocate_marks, build_paper, ProviderError

@pytest.mark.parametrize('weights,total',[([1,1,1],3),([5,10,15],20),([100,1],2),([1]*12,200),([1,1],15)])
def test_positive_exact_allocation(weights,total):
    marks=allocate_marks(weights,total)
    assert sum(marks)==total
    assert len(marks)==len(weights)
    assert min(marks)>=1

def test_impossible_allocation_fails_without_loop():
    with pytest.raises(ValueError):allocate_marks([1,1,1],2)

@pytest.mark.parametrize('marks,count',[(0,2),(-1,2),(1,2),(15,0),(15,13)])
def test_invalid_blueprint_rejected(marks,count):
    with pytest.raises(ValidationError):
        GenerateRequest(upload_id=uuid4(),total_marks=max(1,marks),units=[{'unit_id':uuid4(),'marks':marks,'questions_per_alternative':count}])

def test_unit_test_requires_two_units_and_sixteen_total_marks():
    ids=[uuid4(),uuid4()]
    request=GenerateRequest(upload_id=uuid4(),paper_format='unit_test',total_marks=16,
        units=[{'unit_id':unit_id,'marks':8,'questions_per_alternative':2} for unit_id in ids])
    assert request.total_marks==16 and len(request.units)==2
    with pytest.raises(ValidationError,match='exactly two units'):
        GenerateRequest(upload_id=uuid4(),paper_format='unit_test',total_marks=16,
            units=[{'unit_id':ids[0],'marks':16,'questions_per_alternative':2}])

@pytest.mark.parametrize('mode',['balanced','random'])
def test_modes_respect_totals_uniqueness_and_source(payload,upload,mode):
    payload['mode']=mode
    request=GenerateRequest.model_validate(payload)
    paper=build_paper(request,upload)
    assert paper['total_marks']==15
    assert paper['units'][0]['marks']==15
    selected=[q for a in paper['units'][0]['alternatives'] for q in a['questions']]
    assert len({q['id'] for q in selected})==4
    for alternative in paper['units'][0]['alternatives']:
        assert sum(q['marks'] for q in alternative['questions'])==15


def test_gemini_cannot_return_foreign_question(payload,upload,monkeypatch):
    from app.services import llm_service
    payload['mode']='gemini'
    monkeypatch.setattr(llm_service,'gemini_selections',lambda *args:[{'unit_id':upload['units'][0]['id'],'alternatives':[[str(uuid4()),str(uuid4())],[str(uuid4()),str(uuid4())]]}])
    with pytest.raises(ProviderError,match='invalid'):
        build_paper(GenerateRequest.model_validate(payload),upload)


def test_balanced_prefers_requested_levels(payload,upload):
    payload['difficulty']='hard'
    paper=build_paper(GenerateRequest.model_validate(payload),upload)
    assert all(q['bloom']>=5 for a in paper['units'][0]['alternatives'] for q in a['questions'])


def test_all_supported_counts_and_totals_have_finite_exact_allocations():
    for count in range(1,13):
        for total in range(count,201):
            result=allocate_marks([i*i+1 for i in range(count)],total)
            assert sum(result)==total and min(result)>=1


@pytest.mark.parametrize('failure',['timeout','network','blocked','invalid_json','missing_candidates'])
def test_gemini_failures_are_actionable(payload,upload,monkeypatch,failure):
    import httpx
    from app.core import config
    from app.services import llm_service
    monkeypatch.setattr(config,'GEMINI_API_KEY','test-key')
    def post(self,url,**kwargs):
        if failure=='timeout':raise httpx.ReadTimeout('test')
        if failure=='network':raise httpx.ConnectError('test')
        if failure=='blocked':return httpx.Response(200,json={'candidates':[{'finishReason':'SAFETY'}]})
        if failure=='invalid_json':return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'not JSON'}]}}]})
        return httpx.Response(200,json={})
    monkeypatch.setattr(httpx.Client,'post',post)
    payload['mode']='gemini'
    with pytest.raises(ProviderError):
        build_paper(GenerateRequest.model_validate(payload),upload)


def test_gemini_transient_error_has_bounded_retry(payload,upload,monkeypatch):
    import httpx
    from app.core import config
    from app.services import llm_service
    monkeypatch.setattr(config,'GEMINI_API_KEY','test-key')
    monkeypatch.setattr(llm_service.time,'sleep',lambda seconds:None)
    calls=[]
    def post(self,url,**kwargs):
        calls.append(url)
        return httpx.Response(429,json={'error':'rate limited'})
    monkeypatch.setattr(httpx.Client,'post',post)
    payload['mode']='gemini'
    with pytest.raises(ProviderError):build_paper(GenerateRequest.model_validate(payload),upload)
    assert len(calls)==2
