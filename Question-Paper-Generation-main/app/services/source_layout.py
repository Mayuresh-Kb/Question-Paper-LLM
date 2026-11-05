"""Recover exam rows and preserve visible source content instead of retyping it."""
import re
from uuid import uuid4
import cv2
import numpy as np
import pymupdf as fitz

MAIN = re.compile(r'^Q\s*\.?\s*\d+\s*[).:]?\s*', re.I)
SUB = re.compile(r'^([a-h])\s*\)\s*', re.I)


def clusters(values, gap=4):
    groups = []
    for value in sorted(values):
        if not groups or value-groups[-1][-1] > gap:
            groups.append([value])
        else:
            groups[-1].append(value)
    return [sum(g)/len(g) for g in groups]


def table_regions(page):
    """Find ruled question/marks tables; require four column boundaries."""
    scale = min(2, (4_000_000/page.rect.get_area())**.5)
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csGRAY)
    arr = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)
    binary = cv2.adaptiveThreshold(arr, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 31, 12)
    vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(20, round(40*scale)))))
    contours, _ = cv2.findContours(vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours]
    boxes = [(x/scale,y/scale,w/scale,h/scale) for x,y,w,h in boxes if h>40*scale and w<8*scale and .03*pix.width<x<.95*pix.width]
    xs = clusters([x for x,y,w,h in boxes], 5)
    if len(xs)<4:
        return []
    left,right = max(zip(xs,xs[1:]), key=lambda p:p[1]-p[0])
    if right-left < page.rect.width*.4 or left == xs[0] or right == xs[-1]:
        return []
    edges = [b for b in boxes if abs(b[0]-left)<5 or abs(b[0]-right)<5]
    top,bottom = min(b[1] for b in edges),max(b[1]+b[3] for b in edges)
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT,(max(20,round(30*scale)),1)))
    x0,x1 = round(left*scale),round(right*scale)
    ys = []
    for y in range(max(0,round(top*scale)),min(pix.height,round(bottom*scale)+1)):
        # Faint rules and shaded row separators both count as boundaries.
        if np.mean(horizontal[y,x0:x1]>0)>.38 or np.mean(arr[y,x0:x1]<230)>.72:
            ys.append(y/scale)
    bands=[]
    for y in sorted([top,bottom]+ys):
        if not bands or y-bands[-1][-1]>4:bands.append([y])
        else:bands[-1].append(y)
    return [fitz.Rect(left+3,a[-1]-1,right-3,b[0]+3) for a,b in zip(bands,bands[1:]) if b[0]-a[-1]>=16]


def exam_lines(lines):
    """Ignore candidate instructions; split a), b), c) into independent questions."""
    explicit = [i for i,line in enumerate(lines) if MAIN.match(line['text'])]
    if not explicit:
        return lines
    result, serial = [],0
    for line in lines[explicit[0]:]:
        value = line['text'].strip()
        if re.match(r'^\[\d{4,}\]-\d+',value) or re.fullmatch(r'[.…\s]+',value):
            continue
        if re.fullmatch(r'OR|P\.?\s*T\.?\s*O\.?',value,re.I):
            continue
        main = MAIN.match(value)
        tail = value[main.end():] if main else value
        sub = SUB.match(tail)
        if main or sub:
            serial += 1
            prefix = (main.end() if main else 0)+(sub.end() if sub else 0)
            result.append({**line,'text':f'{serial}. '+value[prefix:], '_prefix':value[:prefix]})
        else:
            result.append(line)
    return result


def save_crop(doc, page_number, rect, asset_dir, masks=()):
    page = doc[page_number]
    rect = rect & page.rect
    if rect.is_empty or rect.height<2:
        return None
    # Render at print resolution, without copying OCR text or substituting fonts.
    scale = min(3, (8_000_000/rect.get_area())**.5)
    pix = page.get_pixmap(matrix=fitz.Matrix(scale,scale), clip=rect, alpha=False)
    for mask in masks:
        r = (fitz.Rect(mask)&rect)*fitz.Matrix(scale,scale)
        r = r.irect
        if not r.is_empty:
            pix.set_rect(r, (255,255,255))
    name = str(uuid4())+'.png'
    pix.save(asset_dir/name)
    return name


def preserve_questions(doc, questions, lines, asset_dir):
    for i,q in enumerate(questions):
        following = questions[i+1] if i+1<len(questions) else None
        first = q['source_page']-1
        last = following['source_page']-1 if following else len(doc)-1
        crops=[]
        for pn in range(first,last+1):
            page=doc[pn]
            top=q['_start'][1]-2 if pn==first else 40
            bottom=following['_start'][1]-3 if following and pn==last else page.rect.height-40
            relevant=[l for l in lines if l['page']==pn+1 and l['bbox'][1]>=top-1 and l['bbox'][1]<bottom]
            if not relevant:
                continue
            def is_furniture(line):
                value=line.get('_original',line['text']).strip()
                return (
                    re.fullmatch(r'OR|P\.?\s*T\.?\s*O\.?|\[\d{1,3}\]',value,re.I)
                    or re.fullmatch(r'[.…*\s]+',value)
                    or (line['bbox'][1] > page.rect.height-100 and (
                        re.search(r'P\.?\s*T\.?\s*O\.?',value,re.I)
                        or re.search(r'\[\d{4,}\]\s*-\s*\d+',value)
                    ))
                )
            content_lines=[line for line in relevant if not is_furniture(line)]
            if not content_lines:
                continue
            # End at the final content line; include nearby figures via source band.
            graphics=[fitz.Rect(d['rect']) for d in page.get_drawings()]
            graphics += [fitz.Rect(d['bbox']) for d in page.get_image_info() if fitz.Rect(d['bbox']).height<page.rect.height*.8]
            graphic_ends=[r.y1 for r in graphics if r.y0>=top and r.y1<bottom and r.y0<page.rect.height-90]
            bottom=min(bottom,max([l['bbox'][3] for l in content_lines]+graphic_ends)+5)
            rect=fitz.Rect(35,top,page.rect.width-35,bottom)
            masks=[]
            for l in relevant:
                v=l.get('_original',l['text']).strip()
                if is_furniture(l):
                    masks.append(l['bbox'])
                # Remove source question labels and metadata using exact word boxes.
                for word in l.get('words',[]):
                    if re.fullmatch(r'(?:Q\.?\d+[).:]?|[a-h]\)|\d+[.)])',word['text'],re.I) and word['bbox'][0]<160:
                        masks.append(word['bbox'])
                    if re.fullmatch(r'\[\d{1,3}\]?|Marks?\]',word['text'],re.I):
                        masks.append(word['bbox'])
            asset=save_crop(doc,pn,rect,asset_dir,masks)
            if asset:crops.append(asset)
        if crops:
            q.update(source_fragments=crops,render_mode='text',source_text=q['text'])
            if q.get('extraction_method')=='ocr':q['source_previews']=crops


def table_questions(doc, lines, asset_dir, parse_lines, ocr_pages=(), budget=None):
    from app.services.ocr import read_region
    records=[]
    for pn,page in enumerate(doc):
        regions=table_regions(page)
        if not regions:
            return None  # Fall back rather than silently omit pages outside the table.
        for rect in regions:
            selected=[]; scores=[]; marks=[]
            for line in lines:
                if line['page']!=pn+1:continue
                words=[w for w in line.get('words',[]) if rect.contains(fitz.Point((w['bbox'][0]+w['bbox'][2])/2,(w['bbox'][1]+w['bbox'][3])/2))]
                if words:
                    selected.append(' '.join(w['text'] for w in words))
                    if line.get('ocr'):scores.append(line['ocr_confidence'])
                for w in line.get('words',[]):
                    if w['bbox'][0]>rect.x1 and rect.y0<(w['bbox'][1]+w['bbox'][3])/2<rect.y1 and re.fullmatch(r'\d{1,2}',w['text']):marks.append(int(w['text']))
            if pn in ocr_pages and rect.height>17:
                try:
                    cell_lines=read_region(page,fitz.Rect(rect.x0,rect.y0+3,rect.x1,rect.y1-3),budget)
                    cell_lines=[l for l in cell_lines if l["ocr_confidence"]>=55]
                    selected=[l['text'] for l in cell_lines]
                    scores=[l['ocr_confidence'] for l in cell_lines]
                    for l in cell_lines:
                        if re.fullmatch(r'OR[\s;:|.]*',l['text'],re.I) and l['bbox'][1] < rect.y0+22:
                            rect.y0=l['bbox'][3]+4
                except ValueError as exc:
                    if 'no readable text' not in str(exc):
                        raise
            if pn in ocr_pages and not selected:
                continue
            value='\n'.join(s for s in selected if not re.fullmatch(r'OR[\s;:|.]*',s,re.I)).strip()
            if len(value)<12 or re.fullmatch(r'(?:Questions?|OR)[\s;:|.]*',value,re.I):continue
            if 'questions'==value.lower():continue
            if not marks and pn in ocr_pages:
                try:
                    mark_lines=read_region(page,fitz.Rect(rect.x1+6,rect.y0,min(page.rect.width-25,rect.x1+90),rect.y1),budget)
                    marks=[int(m) for l in mark_lines for m in re.findall(r'\b\d{1,2}\b',l['text'])]
                except ValueError as exc:
                    if 'no readable text' not in str(exc):raise
            mark=next((m for m in marks if 1<=m<=200),1)
            qs,_=parse_lines([{'text':'1. '+value+f' [{mark} Marks]','page':pn+1,'bbox':list(rect)}])
            q=qs[0]
            asset=save_crop(doc,pn,rect,asset_dir)
            q.update(source_fragments=[asset],render_mode='text',source_text=q['text'],source_previews=[asset],
                     extraction_method='ocr' if scores else 'text',ocr_confidence=min(scores) if scores else None)
            if not marks:q['marks_source']='default'
            records.append(q)
    return records or None
