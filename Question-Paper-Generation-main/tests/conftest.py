from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.core import config
from main import app

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'UPLOAD_DIR', tmp_path/'sessions')
    monkeypatch.setattr(config, 'OUT_DIR', tmp_path/'papers')
    monkeypatch.setattr(config, 'GEMINI_API_KEY', '')
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def bank_text():
    verbs=['Define','Explain','Apply','Analyze','Evaluate','Design','Describe','Calculate','Compare','Create','List','Justify']
    return '\n'.join(f'{i+1}. {v} the properties of concept {i+1}. [{(i%4)+3} Marks] [BTL: {i%6+1}] [Topic: Topic {i%3}]' for i,v in enumerate(verbs))

@pytest.fixture
def upload(client, bank_text):
    response=client.post('/upload', files=[('files',('bank.txt',bank_text.encode(),'text/plain'))])
    assert response.status_code==200, response.text
    return response.json()

@pytest.fixture
def token(upload):
    return {'X-Session-Token':upload['session_token']}

@pytest.fixture
def payload(upload):
    return {'upload_id':upload['upload_id'], 'total_marks':15, 'mode':'balanced',
            'units':[{'unit_id':upload['units'][0]['id'], 'marks':15, 'questions_per_alternative':2}],
            'header':{'institution':'College <Engineering> & Science', 'exam_name':'Mid Term', 'subject':'Data Structures',
                      'date':'2026-10-05','duration':'1 hour','instructions':'Use a < b where appropriate.\nShow your work.'}}
