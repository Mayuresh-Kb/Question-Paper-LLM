from pathlib import Path
import fitz
import pytest
from docx import Document
from app.services.parser import parse_lines, parse_document

@pytest.mark.parametrize('number',['1.','10)','100.','Q1.','Q.10.','Question 12:','Q 7'])
def test_numbering(number):
    questions,_=parse_lines([f'{number} Define a binary search tree. [5 Marks]'])
    assert len(questions)==1
    assert questions[0]['text']=='Define a binary search tree.'
    assert questions[0]['source_marks']==5

def test_inline_marks_do_not_consume_next_question():
    questions,_=parse_lines(['Q1. Explain the concept of hashing. [5 Marks]','Q2. Describe the structure of trees. [10 Marks]'])
    assert [q['source_marks'] for q in questions]==[5,10]
    assert len(questions)==2

def test_metadata_multiline_and_separate_marks():
    questions,warnings=parse_lines(['1. Explain trees and','their applications.','(8)','[BTL: 2] [Topic: Trees]','2. Design a graph library. [7] [BTL: 6]'])
    assert questions[0]['source_marks']==8
    assert questions[0]['topic']=='Trees'
    assert questions[1]['bloom']==6
    assert not warnings

def test_duplicate_and_missing_metadata_are_visible():
    questions,warnings=parse_lines(['1. Explain linked lists.','2. Explain linked lists.'])
    assert [q['enabled'] for q in questions]==[True,False]
    assert questions[0]['bloom_source']=='estimated'
    assert questions[0]['marks_source']=='default'
    assert warnings

def test_question_without_number_is_not_invented():
    with pytest.raises(ValueError,match='No numbered'):
        parse_lines(['These are teaching notes, not a question bank.'])

def test_broken_or_incomplete_questions_are_disabled_for_review():
    questions,warnings=parse_lines(['1. |||||||||||||| [5 Marks]','2. Explain the following [5 Marks]'])
    assert [q['enabled'] for q in questions]==[False,False]
    assert all(q['quality_issues'] for q in questions)
    assert any('disabled' in warning for warning in warnings)

def test_legacy_symbol_font_characters_become_unicode_math():
    questions,_=parse_lines(['1. Calculate the area using r² for the given circle. [5 Marks]'])
    assert questions[0]['text']=='Calculate the area using πr² for the given circle.'
    assert questions[0]['enabled'] is True

def test_pdf_extracts_vector_figure(tmp_path):
    path=tmp_path/'diagram.pdf'
    with fitz.open() as doc:
        page=doc.new_page()
        page.insert_text((50,60),'1. Explain the following system. [5 Marks]')
        page.draw_rect(fitz.Rect(60,95,150,135),color=(0,0,0))
        page.insert_text((70,120),'Server')
        page.insert_text((50,180),'2. Describe this other system. [5 Marks]')
        doc.save(path)
    questions,warnings=parse_document(path,tmp_path/'assets')
    assert len(questions)==2
    assert questions[0]['assets']
    assert not questions[1]['assets']
    assert (tmp_path/'assets'/questions[0]['assets'][0]).exists()
    assert any('figures' in w for w in warnings)

def test_scan_rejected(tmp_path):
    path=tmp_path/'scan.pdf'
    with fitz.open() as doc:
        doc.new_page();doc.save(path)
    with pytest.raises(ValueError,match='OCR'):
        parse_document(path,tmp_path/'assets')

def test_docx_paragraphs_and_table(tmp_path):
    path=tmp_path/'bank.docx';doc=Document()
    doc.add_paragraph('1. Describe the concept of hashing. [5 Marks]')
    table=doc.add_table(rows=1,cols=3)
    for cell,value in zip(table.rows[0].cells,['2','Explain balanced search trees.','7']):cell.text=value
    doc.save(path)
    questions,_=parse_document(path,tmp_path/'assets')
    assert [q['source_marks'] for q in questions]==[5,7]

@pytest.mark.parametrize('name',['aiml_mark_clean','blockchain_mark_clean'])
def test_supplied_clean_question_banks(name,tmp_path):
    path=next((Path(__file__).parents[1]/'storage/uploads').glob(f'*_{name}.pdf'))
    questions,_=parse_document(path,tmp_path/'assets')
    assert len(questions)>=20
    assert all(q['marks_source']=='provided' for q in questions)
    assert all(not q['text'].startswith('Q.') for q in questions)
