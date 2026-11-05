from pathlib import Path
import cv2
import numpy as np
import pymupdf as fitz
from app.services.parser import parse_document
from app.services.pdf_builder import build_questionpaper_from_json
from app.schemas.models import HeaderModel


def test_exam_instructions_not_questions_and_output_is_selectable_text(tmp_path):
    source=tmp_path/'exam.pdf'
    with fitz.open() as doc:
        p=doc.new_page()
        p.insert_text((50,50),'Instructions:')
        p.insert_text((50,70),'1) Answer any two questions.')
        p.insert_text((50,130),'Q1) a) Evaluate the following expression. [5]')
        p.insert_text((100,160),'x + 1',fontsize=14)
        p.draw_line((95,170),(145,170))
        p.insert_text((105,190),'x - 1',fontsize=14)
        p.insert_text((50,240),'b) Trace this program. [5]')
        p.insert_text((90,265),'for (int i=0; i<3; ++i) {\n    cout << i;\n}',fontname='cour',fontsize=12)
        p.insert_text((50,350),'Q2) a) Explain operator overloading. [5]')
        p.insert_text((50,390),'b) Describe exception handling. [5]')
        doc.save(source)
    assets=tmp_path/'assets'
    qs,_=parse_document(source,assets)
    assert len(qs)==4
    assert all('Answer any' not in q['text'] for q in qs)
    assert all(q['render_mode']=='text' and q['source_fragments'] for q in qs)
    for q in qs:q['marks']=5
    paper={'header':HeaderModel().model_dump(),'total_marks':10,'units':[{'name':'Unit 1','marks':10,'alternatives':[{'number':1,'questions':qs[:2]},{'number':2,'questions':qs[2:]}]}]}
    out=tmp_path/'paper.pdf'
    build_questionpaper_from_json(paper,out,assets)
    with fitz.open(out) as doc:
        text='\n'.join(page.get_text() for page in doc)
        images=[cv2.imdecode(np.frombuffer(doc.extract_image(item[0])['image'],np.uint8),cv2.IMREAD_COLOR) for page in doc for item in page.get_images()]
        assert 'Evaluate the following expression.' in text
        assert 'Trace this program.' in text
        assert 'Total marks:' in text
        assert len(images)<4  # Source text crops must never be embedded as pages of text.


def test_edited_text_mode_does_not_print_original(tmp_path):
    paper={'header':HeaderModel().model_dump(),'total_marks':5,'units':[{'name':'Unit','marks':5,'alternatives':[{'number':1,'questions':[{'text':'Corrected wording','marks':5,'render_mode':'text','source_fragments':['missing.png']}]}]}]}
    build_questionpaper_from_json(paper,tmp_path/'text.pdf',tmp_path)
    with fitz.open(tmp_path/'text.pdf') as doc:
        assert 'Corrected wording' in doc[0].get_text()
        assert not doc[0].get_images()


def test_source_mask_coordinates(tmp_path):
    from app.services.source_layout import save_crop
    with fitz.open() as doc:
        p=doc.new_page();p.draw_rect((100,200,150,240),color=None,fill=(0,0,0))
        name=save_crop(doc,0,fitz.Rect(80,180,180,280),tmp_path,[(99,199,151,241)])
    pixels=cv2.imread(str(tmp_path/name))
    assert np.min(pixels)==255


def test_merged_page_footer_is_removed_from_source_fragment(tmp_path):
    path=tmp_path/'footer.pdf'
    with fitz.open() as doc:
        p=doc.new_page()
        p.insert_text((50,100),'Q1) a) Explain streams. [5]')
        p.insert_text((50,160),'b) Describe files. [5]')
        p.insert_text((50,760),'P.T.O.        [6261]-42        1')
        p2=doc.new_page()
        p2.insert_text((50,100),'Q2) a) Explain exceptions. [5]')
        p2.insert_text((50,160),'b) Describe templates. [5]')
        doc.save(path)
    assets=tmp_path/'assets'
    qs,_=parse_document(path,assets)
    footer_question=qs[1]
    pixels=cv2.imread(str(assets/footer_question['source_fragments'][0]),cv2.IMREAD_GRAYSCALE)
    # The merged footer is excluded from the crop altogether, preventing a
    # blank overflow page that contains only a watermark or page furniture.
    assert pixels.shape[0] < 120


def test_end_marker_does_not_create_blank_overflow_page(tmp_path):
    path=tmp_path/'end-marker.pdf'
    with fitz.open() as doc:
        p=doc.new_page()
        p.insert_text((50,100),'Q1) a) Explain iterators. [5]')
        p.insert_text((50,160),'b) Write a short program. [5]')
        p.insert_text((270,400),'* * *')
        p.insert_text((50,760),'[6261]-42 1')
        doc.save(path)
    assets=tmp_path/'assets'
    qs,_=parse_document(path,assets)
    assert len(qs)==2
    pixels=cv2.imread(str(assets/qs[-1]['source_fragments'][0]),cv2.IMREAD_GRAYSCALE)
    assert pixels.shape[0] < 120


def test_ruled_exam_table_extracts_cells_without_labels_or_marks(tmp_path):
    path=tmp_path/'table.pdf'
    with fitz.open() as doc:
        p=doc.new_page()
        p.insert_text((40,50),'1. Read the instructions carefully.')
        for x in [40,90,450,535]:p.draw_line((x,100),(x,360))
        for y in [100,130,190,250,310,360]:p.draw_line((40,y),(535,y))
        p.insert_text((160,120),'Questions');p.insert_text((470,120),'Marks')
        for i,y in enumerate([150,210,270,330]):
            p.insert_text((50,y),str(i+1))
            p.insert_text((100,y),f'Explain concept {i+1} and give an example.')
            p.insert_text((480,y),'6')
        doc.save(path)
    qs,_=parse_document(path,tmp_path/'assets')
    assert len(qs)==4
    assert [q['source_marks'] for q in qs]==[6]*4
    assert all(q['text'].startswith('Explain concept') for q in qs)
    assert all('instructions' not in q['text'] for q in qs)


def test_tall_source_image_splits_without_losing_pixels(tmp_path):
    from app.services.pdf_builder import SourceExcerpt
    pixels=np.full((3000,800,3),255,dtype=np.uint8)
    pixels[20:100]=0;pixels[1700:1800]=0
    flow=SourceExcerpt(pixels,400)
    pieces=flow.split(400,600)
    assert len(pieces)==2
    assert np.array_equal(np.concatenate([p.pixels for p in pieces]),pixels)
