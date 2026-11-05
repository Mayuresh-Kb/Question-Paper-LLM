"""Bounded, local OCR of printed PDF pages using Tesseract TSV output."""
import csv
import io
import os
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from tempfile import TemporaryDirectory
from pathlib import Path

import pymupdf as fitz
from app.core import config

_slots = threading.BoundedSemaphore(2)


def available():
    return shutil.which(config.TESSERACT_CMD) is not None


@dataclass
class OCRBudget:
    pages: int = 0
    deadline: float = field(default_factory=lambda: time.monotonic() + config.OCR_UPLOAD_TIMEOUT)


def read_page(page, budget, *, count_page=True, psm=3):
    if not available():
        raise ValueError('OCR is unavailable. Install Tesseract with English language data on the backend, then retry this scanned PDF.')
    if count_page and budget.pages >= config.OCR_MAX_PAGES:
        raise ValueError(f'OCR is limited to {config.OCR_MAX_PAGES} pages per upload. Split the scanned bank into smaller files/uploads.')
    remaining = budget.deadline - time.monotonic()
    if remaining <= 0:
        raise ValueError('OCR exceeded the upload time limit. Retry with fewer scanned pages.')
    if not _slots.acquire(blocking=False):
        raise ValueError('OCR is busy processing other scans. Please retry shortly.')
    if count_page:
        budget.pages += 1
    try:
        # Bound pixel allocation before rendering unusually large PDF page sizes.
        scale = min(300 / 72, (config.OCR_MAX_PIXELS / page.rect.get_area()) ** 0.5)
        with TemporaryDirectory(prefix='question-ocr-') as temp:
            path = Path(temp) / 'page.png'
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csGRAY, alpha=False)
            pix.save(path)
            remaining = budget.deadline - time.monotonic()
            if remaining <= 0:
                raise ValueError('OCR exceeded the upload time limit. Retry with fewer scanned pages.')
            try:
                result = subprocess.run(
                    [config.TESSERACT_CMD, str(path), 'stdout', '-l', config.OCR_LANGUAGE,
                     '--dpi', str(max(70, round(72 * scale))), '--psm', str(psm), 'tsv'],
                    capture_output=True, text=True, encoding='utf-8', errors='replace',
                    timeout=min(config.OCR_PAGE_TIMEOUT, remaining),
                    env={**os.environ, 'OMP_THREAD_LIMIT': '1'}, check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise ValueError(f'OCR timed out on page {page.number+1}. Use a clearer scan or fewer pages.') from exc
            except OSError as exc:
                raise ValueError('The OCR engine could not start. Check the backend Tesseract installation.') from exc
            if result.returncode:
                raise ValueError('OCR failed. Check that Tesseract and the configured language data are installed, or try a clearer scan.')
            return parse_tsv(result.stdout, page, pix.width, pix.height)
    finally:
        _slots.release()


def parse_tsv(output, page, width, height):
    groups = {}
    for row in csv.DictReader(io.StringIO(output), delimiter='\t', quoting=csv.QUOTE_NONE):
        if row.get('level') != '5' or not row.get('text', '').strip():
            continue
        key = tuple(row[k] for k in ('block_num', 'par_num', 'line_num'))
        groups.setdefault(key, []).append(row)
    lines = []
    for words in groups.values():
        boxes = [fitz.Rect(float(w['left']), float(w['top']), float(w['left'])+float(w['width']), float(w['top'])+float(w['height'])) for w in words]
        box = fitz.Rect(boxes[0])
        for other in boxes[1:]:
            box |= other
        # OCR coordinates are on the displayed (rotated) page. Convert back to
        # PDF coordinates to agree with native text extraction and source bands.
        box = fitz.Rect(box.x0*page.rect.width/width, box.y0*page.rect.height/height,
                        box.x1*page.rect.width/width, box.y1*page.rect.height/height) * page.derotation_matrix
        confidences = [float(w['conf']) for w in words if float(w['conf']) >= 0]
        lines.append({'text': ' '.join(w['text'] for w in words), 'page': page.number+1,
                      'bbox': list(box), 'ocr': True,
                      'ocr_confidence': round(sum(confidences)/len(confidences), 1) if confidences else 0,
                      'words': [{'text': w['text'], 'bbox': list(fitz.Rect(float(w['left'])*page.rect.width/width, float(w['top'])*page.rect.height/height, (float(w['left'])+float(w['width']))*page.rect.width/width, (float(w['top'])+float(w['height']))*page.rect.height/height)*page.derotation_matrix)} for w in words]})
    if not lines:
        raise ValueError(f'OCR found no readable text on page {page.number+1}. Use a clearer, upright printed scan; handwriting is not supported.')
    return lines


def read_region(page, rect, budget):
    with fitz.open() as region_doc:
        cropped=region_doc.new_page(width=rect.width,height=rect.height)
        cropped.show_pdf_page(cropped.rect,page.parent,page.number,clip=rect)
        lines=read_page(cropped,budget,count_page=False,psm=6)
        for line in lines:
            line['page']=page.number+1
            for item in [line]+line.get('words',[]):
                box=fitz.Rect(item['bbox'])
                item['bbox']=[box.x0+rect.x0,box.y0+rect.y0,box.x1+rect.x0,box.y1+rect.y0]
        return lines
