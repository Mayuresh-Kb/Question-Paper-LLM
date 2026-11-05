"""Exercise a real raster-only bank as well as OCR failure/boundary cases."""
import subprocess
import time
from pathlib import Path

import pymupdf as fitz
import pytest
from app.core import config
from app.services import ocr, parser


@pytest.fixture
def scan(tmp_path):
    path = tmp_path / 'printed-scan.pdf'
    with fitz.open() as source, fitz.open() as target:
        page = source.new_page()
        for i, text in enumerate([
            '1. Explain binary search trees. [5 Marks]',
            '2. Describe the use of a stack. [5 Marks]',
            '3. Compare arrays and linked lists. [5 Marks]',
            '4. Define a queue and its operations. [5 Marks]',
        ]):
            page.insert_text((50, 90+i*100), text, fontsize=16)
        target.new_page().insert_image(page.rect, stream=page.get_pixmap(matrix=fitz.Matrix(2, 2)).tobytes('png'))
        target.save(path)
    return path


@pytest.mark.skipif(not ocr.available(), reason='Tesseract required for real OCR integration')
def test_real_scan_upload_review_generate_download(client, scan):
    with fitz.open(scan) as doc:
        assert not doc[0].get_text().strip()
    response = client.post('/upload', files=[('files', (scan.name, scan.read_bytes(), 'application/pdf'))])
    assert response.status_code == 200, response.text
    session = response.json()
    unit = session['units'][0]
    assert len(unit['questions']) == 4
    assert [q['source_marks'] for q in unit['questions']] == [5]*4
    assert 'binary search trees' in unit['questions'][0]['text']
    assert all(q['extraction_method'] == 'ocr' and q['source_previews'] for q in unit['questions'])
    assert all(not q['assets'] for q in unit['questions'])  # A full scan must not become a figure.
    token = {'X-Session-Token': session['session_token']}
    asset = unit['questions'][0]['source_previews'][0].removesuffix('.png')
    url = f"/uploads/{session['upload_id']}/assets/{asset}"
    assert client.get(url, headers=token).headers['content-type'] == 'image/png'
    assert client.get(url, headers={'X-Session-Token': 'wrong'}).status_code == 403
    response = client.post('/generate', headers=token, json={
        'upload_id': session['upload_id'], 'total_marks': 10,
        'units': [{'unit_id': unit['id'], 'marks': 10, 'questions_per_alternative': 2}],
    })
    assert response.status_code == 200, response.text
    pdf = client.get('/download/'+response.json()['pdf_id'], headers=token)
    with fitz.open(stream=pdf.content, filetype='pdf') as doc:
        text = '\n'.join(page.get_text() for page in doc)
        assert sum(len(p.get_images()) for p in doc) == 0
        assert 'Total marks:' in text
        assert 'binary search trees' in text
        assert all(q['render_mode'] == 'text' for q in unit['questions'])


def fake_read(page, budget):
    budget.pages += 1
    return [{'text': f'{page.number+1}. Explain trees. [5 Marks]', 'page': page.number+1,
             'bbox': [50, 50, 300, 70], 'ocr': True, 'ocr_confidence': 60}]


def test_mixed_pages_and_low_confidence(scan, tmp_path, monkeypatch):
    path = tmp_path/'mixed.pdf'
    with fitz.open(scan) as doc:
        doc.new_page().insert_text((50, 60), '2. Describe graphs. [4 Marks]')
        doc.save(path)
    monkeypatch.setattr(parser, 'read_page', fake_read)
    questions, warnings = parser.parse_document(path, tmp_path/'assets')
    assert [q['extraction_method'] for q in questions] == ['ocr', 'text']
    assert any('low recognition' in w for w in warnings)
    assert questions[0]['source_previews']
    assert not questions[1].get('source_previews')


def test_native_text_bypasses_ocr_and_force_replaces_it(tmp_path, monkeypatch):
    path = tmp_path/'native.pdf'
    with fitz.open() as doc:
        doc.new_page().insert_text((50, 60), '1. Define native text. [5 Marks]')
        doc.save(path)
    calls = []
    def read(page, budget):
        calls.append(page.number)
        return fake_read(page, budget)
    monkeypatch.setattr(parser, 'read_page', read)
    questions, _ = parser.parse_document(path, tmp_path/'a')
    assert not calls and questions[0]['extraction_method'] == 'text'
    questions, _ = parser.parse_document(path, tmp_path/'b', 'force')
    assert calls == [0] and questions[0]['text'] == 'Explain trees.'


def test_scan_with_header_still_uses_ocr(scan, tmp_path, monkeypatch):
    path = tmp_path/'header.pdf'
    with fitz.open(scan) as doc:
        doc[0].insert_text((20, 20), 'Digital header')
        doc.save(path)
    monkeypatch.setattr(parser, 'read_page', fake_read)
    questions, _ = parser.parse_document(path, tmp_path/'assets')
    assert questions[0]['extraction_method'] == 'ocr'


def test_unavailable_ocr_rolls_back_upload(client, scan, monkeypatch):
    monkeypatch.setattr(config, 'TESSERACT_CMD', '/missing/tesseract')
    assert client.get('/health').json()['ocr_available'] is False
    response = client.post('/upload', files=[('files', (scan.name, scan.read_bytes(), 'application/pdf'))])
    assert response.status_code == 400
    assert 'Install Tesseract' in response.json()['detail']
    assert not list(config.UPLOAD_DIR.iterdir())


@pytest.mark.parametrize('failure', ['timeout', 'failed', 'empty'])
def test_engine_failures(scan, monkeypatch, failure):
    monkeypatch.setattr(ocr, 'available', lambda: True)
    def run(*args, **kwargs):
        if failure == 'timeout':
            raise subprocess.TimeoutExpired('tesseract', 1)
        return subprocess.CompletedProcess(args[0], 1 if failure == 'failed' else 0, '', '')
    monkeypatch.setattr(ocr.subprocess, 'run', run)
    with fitz.open(scan) as doc, pytest.raises(ValueError, match='OCR'):
        ocr.read_page(doc[0], ocr.OCRBudget())


def test_page_and_time_budgets(scan, monkeypatch):
    monkeypatch.setattr(ocr, 'available', lambda: True)
    with fitz.open(scan) as doc:
        with pytest.raises(ValueError, match='limited'):
            ocr.read_page(doc[0], ocr.OCRBudget(pages=config.OCR_MAX_PAGES))
        with pytest.raises(ValueError, match='time limit'):
            ocr.read_page(doc[0], ocr.OCRBudget(deadline=time.monotonic()-1))


def test_invalid_ocr_mode(client, bank_text):
    response = client.post('/upload', data={'ocr_mode': 'shell'}, files=[('files', ('bank.txt', bank_text.encode(), 'text/plain'))])
    assert response.status_code == 422
