"""Parse explicit numbered question banks, preserving source and figure references.

Supported metadata: [5 Marks] [BTL: 3] [Topic: Trees]. Printed scans use local OCR with explicit review warnings.
The parser never silently invents a question or a pedagogical classification.
"""
import re
from collections import Counter
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile, BadZipFile

import pymupdf as fitz
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.core import config
from app.services.diagram_extractor import attach_pdf_figures
from app.services.ocr import OCRBudget, read_page
from app.services.question_quality import question_quality_issues
from app.services.source_layout import exam_lines, table_questions, preserve_questions
from app.services.text_normalization import normalize_legacy_symbols

START = re.compile(r"^\s*(?:(?:Q(?:uestion)?\s*\.?\s*\d{1,3})\s*[).:\-]?|\d{1,3}\s*[).])\s*", re.I)
MARKS = re.compile(r"(?:\[\s*(\d{1,3})\s*(?:marks?|m)?\s*\]|\(\s*(\d{1,3})\s*(?:marks?|m)?\s*\)|\b(\d{1,3})\s*(?:marks?|m)\b)\s*$", re.I)
MARKS_ONLY = re.compile(r"^(?:marks?\s*:\s*)?[\[(]?\s*(\d{1,3})\s*(?:marks?|m)?\s*[\])]?\s*$", re.I)
BLOOM = re.compile(r"\[\s*(?:bloom|btl|level)\s*:?\s*([1-6])\s*\]", re.I)
TOPIC = re.compile(r"\[\s*topic\s*:\s*([^\]]+)\]", re.I)
PAGE = re.compile(r"^(?:page\s+\d+(?:\s+of\s+\d+)?|\d+\s*/\s*\d+)\s*$", re.I)


def normalized_text(text):
    return re.sub(r"\W+", " ", text.casefold()).strip()


def estimate_bloom(text):
    # An explicitly labelled heuristic, editable by the teacher before generation.
    levels = [(6, r"\b(design|create|develop|compose|formulate)\b"),
              (5, r"\b(evaluate|justify|critique|assess|recommend)\b"),
              (4, r"\b(analy[sz]e|compare|differentiate|contrast|examine)\b"),
              (3, r"\b(solve|calculate|apply|demonstrate|implement|compute)\b"),
              (2, r"\b(explain|describe|summari[sz]e|discuss|illustrate)\b")]
    for level, pattern in levels:
        if re.search(pattern, text, re.I):
            return level
    return 1


def parse_lines(lines):
    """Lines may include PDF coordinates or DOCX assets. Return questions + warnings."""
    questions, warnings, current = [], [], None

    def finish():
        if not current:
            return
        text = "\n".join(current["parts"]).strip("\n")
        if len(text) < 3:
            warnings.append("An empty numbered question was skipped.")
            return
        missing_marks = current["marks"] is None
        if missing_marks:
            warnings.append(f"Question {len(questions)+1}: no marks found; review the default of 1 mark.")
        bloom = current["bloom"] or estimate_bloom(text)
        quality_issues = question_quality_issues(text)
        questions.append({
            "id": str(uuid4()), "text": text, "source_marks": current["marks"] or 1,
            "bloom": bloom, "bloom_source": "provided" if current["bloom"] else "estimated",
            "marks_source": "default" if missing_marks else "provided", "topic": current["topic"],
            "enabled": not quality_issues, "include_figures": True, "assets": current["assets"],
            "render_mode": "text", "quality_issues": quality_issues,
            "source_page": current["page"], "_start": current["start"],
            "extraction_method": "ocr" if current["confidences"] else "text",
            "ocr_confidence": min(current["confidences"]) if current["confidences"] else None,
        })

    for item in lines:
        item = {"text": item} if isinstance(item, str) else item
        text = normalize_legacy_symbols(item["text"]).rstrip()
        if PAGE.fullmatch(text):
            continue
        start = START.match(text)
        if start:
            finish()
            current = {"parts": [], "marks": None, "bloom": None, "topic": "", "assets": [],
                       "page": item.get("page"), "start": item.get("bbox"), "confidences": []}
            text = text[start.end():].strip()
        if current is None:
            continue
        current["assets"].extend(item.get("assets", []))
        if item.get("ocr"):
            current["confidences"].append(item["ocr_confidence"])
        b = BLOOM.search(text)
        if b:
            current["bloom"] = int(b.group(1))
            text = BLOOM.sub("", text).strip()
        topic = TOPIC.search(text)
        if topic:
            current["topic"] = topic.group(1).strip()[:150]
            text = TOPIC.sub("", text).strip()
        # A standalone numeric line after existing marks is usually a page number.
        only = MARKS_ONLY.fullmatch(text)
        if only and current["parts"]:
            if current["marks"] is None:
                value = int(only.group(1))
                if not 1 <= value <= 200:
                    raise ValueError("Source marks must be between 1 and 200.")
                current["marks"] = value
            continue
        inline = MARKS.search(text)
        if inline:
            value = int(next(g for g in inline.groups() if g is not None))
            if not 1 <= value <= 200:
                raise ValueError("Source marks must be between 1 and 200.")
            current["marks"] = value
            text = text[:inline.start()].strip()
        if text:
            current["parts"].append(text)
    finish()
    if not questions:
        raise ValueError("No numbered questions found. Start questions with Q1., 1., or 1), and add marks such as [5 Marks].")
    if len(questions) > config.MAX_QUESTIONS:
        raise ValueError(f"Each unit may contain at most {config.MAX_QUESTIONS} questions.")
    seen = set()
    for question in questions:
        key = normalized_text(question["text"])
        if key in seen:
            question["enabled"] = False
            warnings.append("A repeated question was disabled. Review the question bank before generating.")
        seen.add(key)
    if any(q["bloom_source"] == "estimated" for q in questions):
        warnings.append("Bloom levels without [BTL: 1-6] tags are estimated from command words. Review these classifications.")
    if any(q["quality_issues"] for q in questions):
        warnings.append("Questions with incomplete or unreadable text were disabled. Correct their text before enabling them.")
    return questions, list(dict.fromkeys(warnings))


def _pdf_lines(doc, ocr_mode="auto", budget=None, ocr_pages=None):
    lines = []
    margin_texts = Counter()
    budget = budget or OCRBudget()
    ocr_pages = ocr_pages if ocr_pages is not None else set()
    for index, page in enumerate(doc):
        page_lines = []
        for block in page.get_text("dict", sort=True)["blocks"]:
            for line in block.get("lines", []):
                if abs(line.get("dir", (1,0))[1]) > .15:
                    continue  # Diagonal watermarks are not question content.
                text = "".join(s["text"] for s in line["spans"]).strip()
                if text:
                    words = [{"text": w[4], "bbox": list(w[:4])} for w in page.get_text("words") if fitz.Rect(w[:4]).intersects(fitz.Rect(line["bbox"])) and abs(w[1]-line["bbox"][1])<4]
                    item = {"text": text, "page": index + 1, "bbox": list(line["bbox"]), "words": words}
                    page_lines.append(item)
                    if line["bbox"][1] < 45 or line["bbox"][3] > page.rect.height - 40:
                        margin_texts[text] += 1
        # Join label/body/marks fragments on the same baseline in reading order.
        merged = []
        for item in sorted(page_lines, key=lambda l:(round(l["bbox"][1]/3), l["bbox"][0])):
            if merged and abs(merged[-1]["bbox"][1]-item["bbox"][1]) < 3:
                previous=merged[-1]
                previous["text"] += " " + item["text"]
                previous["words"] += item["words"]
                previous["bbox"] = list(fitz.Rect(previous["bbox"]) | fitz.Rect(item["bbox"]))
            else: merged.append(item)
        page_lines=merged
        images = page.get_image_info()
        # A full-page image can have a misleading header/footer text layer.
        image_area = sum((fitz.Rect(i["bbox"]) & page.rect).get_area() for i in images)
        needs_ocr = image_area >= page.rect.get_area() * .5 or (not page_lines and (images or page.get_drawings()))
        if needs_ocr or (ocr_mode == "force" and (page_lines or images or page.get_drawings())):
            page_lines = read_page(page, budget)
            ocr_pages.add(index)
        for item in page_lines:
            if item["bbox"][1] < 45 or item["bbox"][3] > page.rect.height - 40:
                if item.get("ocr"):
                    margin_texts[item["text"]] += 1
        lines.extend(page_lines)
    if not lines:
        raise ValueError("No extractable text found. Empty PDFs cannot be used; OCR needs a visible printed page.")
    return [line for line in lines if not (margin_texts[line["text"]] > 1 and not START.match(line["text"]))]



def _docx_lines(path, asset_dir):
    try:
        with ZipFile(path) as z:
            if sum(i.file_size for i in z.infolist()) > 50 * 1024 * 1024:
                raise ValueError("DOCX expands beyond the 50 MB processing limit.")
        doc = Document(path)
    except (BadZipFile, KeyError) as exc:
        raise ValueError("This is not a valid DOCX file.") from exc
    lines = []
    for block in doc.iter_inner_content():
        if isinstance(block, Table):
            for row in block.rows:
                values = [c.text.strip() for c in row.cells]
                if len(values) >= 2 and values[0].isdigit():
                    text = values[0]+". "+values[1]
                    if len(values) > 2 and values[2].isdigit():
                        text += " ["+values[2]+" Marks]"
                    lines.append({"text": text})
                else:
                    lines.extend({"text": v} for v in values if v)
        elif isinstance(block, Paragraph):
            assets = []
            for blip in block._p.xpath('.//a:blip'):
                relation = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                if relation:
                    data = doc.part.related_parts[relation].blob
                    try:
                        pix = fitz.Pixmap(data)
                        if pix.width * pix.height > 20_000_000:
                            raise ValueError("An embedded image is too large.")
                        if pix.colorspace and pix.colorspace.n > 3:
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                        asset = str(uuid4()) + ".png"
                        pix.save(asset_dir / asset)
                        assets.append(asset)
                    except RuntimeError as exc:
                        raise ValueError("An embedded DOCX image could not be read. Convert it to PNG or JPEG.") from exc
            chunks = block.text.splitlines() or [""]
            lines.extend({"text": s, "assets": assets if i == len(chunks)-1 else []} for i, s in enumerate(chunks))
    return lines


def parse_document(path: Path, asset_dir: Path, ocr_mode="auto", ocr_budget=None):
    asset_dir.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            with fitz.open(path) as doc:
                if doc.needs_pass:
                    raise ValueError("Password-protected PDFs are not supported. Upload an unlocked copy.")
                if not 1 <= len(doc) <= config.MAX_PAGES:
                    raise ValueError(f"PDFs must have between 1 and {config.MAX_PAGES} pages.")
                ocr_pages = set()
                ocr_budget = ocr_budget or OCRBudget()
                lines = _pdf_lines(doc, ocr_mode, ocr_budget, ocr_pages)
                questions = table_questions(doc, lines, asset_dir, parse_lines, ocr_pages, ocr_budget)
                warnings = []
                if questions is None:
                    prepared = exam_lines(lines)
                    questions, warnings = parse_lines(prepared)
                    attach_pdf_figures(doc, questions, asset_dir, skip_pages=ocr_pages)
                    # Use the unmodified PDF lines for cropping.  The prepared
                    # lines intentionally omit source OR/P.T.O. furniture, but
                    # the cropper still needs those boxes so it can mask them.
                    preserve_questions(doc, questions, lines, asset_dir)
                if len(questions) > config.MAX_QUESTIONS:
                    raise ValueError(f"Each unit may contain at most {config.MAX_QUESTIONS} questions.")
                if any(q['marks_source']=='default' for q in questions):
                    warnings.append("Some source marks could not be read and defaulted to 1. Correct Source marks against the excerpt before generating.")
                if any(q['bloom_source']=='estimated' for q in questions):
                    warnings.append("Bloom levels are estimates. Review them before generation.")
                warnings.append("PDF questions print as selectable text. Compare extracted wording, equations and symbols with the source preview before generating.")
                if ocr_pages:
                    warnings.append("Scanned pages are converted to selectable text with OCR. Correct every recognition error against the source preview before generating.")
                    if any(q.get("ocr_confidence") is not None and q["ocr_confidence"] < 80 for q in questions):
                        warnings.append("Some OCR text has low recognition confidence. Check its original source excerpt.")
        except (fitz.FileDataError, fitz.EmptyFileError) as exc:
            raise ValueError("The uploaded file is not a readable PDF.") from exc
    elif suffix == ".docx":
        questions, warnings = parse_lines(_docx_lines(path, asset_dir))
    elif suffix == ".txt":
        try:
            questions, warnings = parse_lines(path.read_text(encoding="utf-8-sig").splitlines())
        except UnicodeDecodeError as exc:
            raise ValueError("Text files must use UTF-8 encoding.") from exc
    else:
        raise ValueError("Supported formats are PDF, DOCX and UTF-8 TXT. Convert older .doc files to DOCX.")
    for question in questions:
        question.pop("_start", None)
    if any(q["assets"] for q in questions):
        warnings.append("Source figures were attached by position. Verify each figure in the review; disable figures if association is incorrect.")
    return questions, warnings


def parse_pdf_to_array(pdf_path: str):
    """Compatibility helper for earlier scripts; the API uses richer question records."""
    with fitz.open(pdf_path) as doc:
        questions, _ = parse_lines(_pdf_lines(doc))
    return [[q["text"], q["source_marks"], q["bloom"]] for q in questions]


def attach_scan_previews(doc, questions, asset_dir, ocr_pages):
    """Review-only crops: never mistake a page scan for a printable diagram."""
    for index, question in enumerate(questions):
        following = questions[index+1] if index+1 < len(questions) else None
        first = question["source_page"] - 1
        last = following["source_page"] - 1 if following else len(doc)-1
        previews = []
        for number in range(first, last+1):
            if number not in ocr_pages:
                continue
            page = doc[number]
            # Rendering clip uses displayed coordinates, unlike extracted bboxes.
            start = fitz.Rect(question["_start"]) * page.rotation_matrix
            top = max(0, start.y0-4) if number == first else 0
            end = fitz.Rect(following["_start"]) * page.rotation_matrix if following else None
            bottom = end.y0-4 if following and number == last else page.rect.height
            clip = fitz.Rect(0, top, page.rect.width, bottom) & page.rect
            if clip.is_empty:
                continue
            scale = min(1.5, (2_000_000/clip.get_area())**.5)
            asset = str(uuid4()) + ".png"
            page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False).save(asset_dir/asset)
            previews.append(asset)
        if previews:
            question["source_previews"] = previews
