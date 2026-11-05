from pathlib import Path
import fitz
import pytest
from app.schemas.models import GenerateRequest
from app.services.llm_service import build_paper
from app.services.pdf_builder import build_questionpaper_from_json


def test_long_question_wraps_across_pages(tmp_path,payload,upload):
    paper=build_paper(GenerateRequest.model_validate(payload),upload)
    paper['units'][0]['alternatives'][0]['questions'][0]['text']='Explain the following case in detail. '+('This is a long but meaningful case description. '*180)+' UNIQUE_END_MARKER'
    path=tmp_path/'long.pdf'
    build_questionpaper_from_json(paper,path)
    with fitz.open(path) as doc:
        text='\n'.join(p.get_text() for p in doc)
        assert len(doc)>1
        assert 'Q1.' in doc[0].get_text()
        assert 'Explain the following case' in doc[0].get_text()
        assert 'UNIQUE_END_MARKER' in text
        assert f'Page {len(doc)}' in text
        for page in doc:
            for word in page.get_text('words'):
                assert 0<=word[0]<word[2]<=page.rect.width+1
                assert 0<=word[1]<word[3]<=page.rect.height+1


def test_unsupported_glyph_is_reported_not_silently_lost(tmp_path,payload,upload):
    paper=build_paper(GenerateRequest.model_validate(payload),upload)
    paper['header']['subject']='Example \U0001f600'
    with pytest.raises(ValueError,match='cannot render'):
        build_questionpaper_from_json(paper,tmp_path/'unsupported.pdf')


def test_two_units_use_q1_or_q2_then_q3_or_q4_as_selectable_text(tmp_path):
    def alternative(number,word):
        return {'number':number,'questions':[{'text':f'Explain the meaning of {word}.','marks':5,'assets':[]}]}
    paper={'header':{'institution':'Institute','exam_name':'Unit Test','subject':'Data Structures',
                     'date':'','duration':'1 hour','instructions':''},'total_marks':10,'units':[
        {'name':'Unit 1','marks':5,'alternatives':[alternative(1,'trees'),alternative(2,'graphs')]},
        {'name':'Unit 2','marks':5,'alternatives':[alternative(3,'stacks'),alternative(4,'queues')]},
    ]}
    path=tmp_path/'unit-test.pdf'
    build_questionpaper_from_json(paper,path)
    with fitz.open(path) as doc:
        extracted='\n'.join(page.get_text() for page in doc)
        labels=['Q1. Unit 1','Q2. Unit 1','Q3. Unit 2','Q4. Unit 2']
        assert all(label in extracted for label in labels)
        assert [extracted.index(label) for label in labels]==sorted(extracted.index(label) for label in labels)
        assert extracted.count('OR')==2
        assert sum(len(page.get_images()) for page in doc)==0


def test_legacy_symbol_pi_is_normalized_and_searchable(tmp_path):
    paper={'header':{'institution':'Institute','exam_name':'Unit Test','subject':'Mathematics',
                     'date':'','duration':'1 hour','instructions':''},'total_marks':5,'units':[
        {'name':'Unit 1','marks':5,'alternatives':[
            {'number':1,'questions':[{'text':'Calculate the area r² of the given circle.','marks':5,'assets':[]}]},
            {'number':2,'questions':[{'text':'Explain how to calculate the circumference of a circle.','marks':5,'assets':[]}]},
        ]}]}
    path=tmp_path/'legacy-symbol.pdf'
    build_questionpaper_from_json(paper,path)
    with fitz.open(path) as doc:
        extracted='\n'.join(page.get_text() for page in doc)
        assert 'πr²' in extracted
        assert '' not in extracted
