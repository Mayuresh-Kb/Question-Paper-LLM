import copy
import logging
import shutil
import threading
import time
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
import pymupdf as fitz
from fastapi.responses import FileResponse, Response

from app.core import config
from app.core.utils import atomic_json, new_token, paper_record, public_session, secure_filename, session_record, download_signature, signed_download_record
from app.schemas.models import BankEdit, GenerateRequest, ReplaceRequest
from app.services.llm_service import ProviderError, build_paper, eligible_questions, refresh_warnings, validate_paper
from app.services.parser import normalized_text, parse_document
from app.services.question_quality import question_quality_issues
from app.services.text_normalization import normalize_legacy_symbols
from app.services.ocr import OCRBudget, available as ocr_available
from app.services.pdf_builder import build_questionpaper_from_json

router = APIRouter()
logger = logging.getLogger("question_paper")
SessionToken = Annotated[str, Header(alias="X-Session-Token")]
record_lock = threading.RLock()
generation_slots = threading.BoundedSemaphore(4)


@router.get("/health")
def health():
    return {"status": "ok", "gemini_configured": bool(config.GEMINI_API_KEY),
            "ocr_available": ocr_available(), "ocr_language": config.OCR_LANGUAGE, "ocr_max_pages": config.OCR_MAX_PAGES,
            "formats": ["pdf", "docx", "txt"], "max_files": config.MAX_FILES,
            "max_file_bytes": config.MAX_FILE_BYTES, "retention_hours": config.RETENTION_HOURS}


@router.post("/upload")
def upload(files: list[UploadFile] = File(...), ocr_mode: Literal["auto", "force"] = Form("auto")):
    """Synchronous handlers run in FastAPI's worker pool, leaving the event loop free."""
    upload_id, (token, digest) = str(uuid4()), new_token()
    directory = config.UPLOAD_DIR / upload_id
    try:
        if not 1 <= len(files) <= config.MAX_FILES:
            raise ValueError(f"Upload between 1 and {config.MAX_FILES} files, one per unit.")
        directory.mkdir(parents=True)
        assets = directory / "assets"
        units, warnings, total_bytes = [], [], 0
        ocr_budget = OCRBudget()
        for index, file in enumerate(files):
            original = secure_filename(file.filename or "")
            suffix = Path(original).suffix.lower()
            if suffix not in (".pdf", ".docx", ".txt"):
                raise ValueError("Only PDF, DOCX and UTF-8 TXT files are supported. Convert .doc files to DOCX.")
            path = directory / (str(uuid4()) + suffix)
            size = 0
            with path.open("wb") as output:
                while chunk := file.file.read(1024*1024):
                    size += len(chunk)
                    total_bytes += len(chunk)
                    if size > config.MAX_FILE_BYTES or total_bytes > 30*1024*1024:
                        raise HTTPException(413, "Files may be at most 10 MB each and 30 MB per upload.")
                    output.write(chunk)
            if not size:
                raise ValueError(f"{original}: the file is empty.")
            try:
                questions, notes = parse_document(path, assets, ocr_mode, ocr_budget)
            except ValueError as exc:
                raise ValueError(f"{original}: {exc}") from exc
            units.append({"id": str(uuid4()), "name": f"Unit {index+1}", "filename": original,
                          "questions": questions, "warnings": notes})
            warnings.extend(f"{original}: {note}" for note in notes)
        record = {"upload_id": upload_id, "token_hash": digest, "units": units, "warnings": warnings,
                  "expires_at": time.time() + config.RETENTION_HOURS*3600}
        atomic_json(directory / "manifest.json", record)
        return {**public_session(record), "session_token": token}
    except HTTPException:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    except ValueError as exc:
        shutil.rmtree(directory, ignore_errors=True)
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        shutil.rmtree(directory, ignore_errors=True)
        logger.exception("Upload processing failed")
        raise HTTPException(400, "The document could not be processed. Check its format or export a text PDF.") from exc
    finally:
        for file in files:
            file.file.close()


@router.get("/uploads/{upload_id}")
def get_upload(upload_id: UUID, x_session_token: SessionToken):
    return public_session(session_record(upload_id, x_session_token))


@router.put("/uploads/{upload_id}/unit")
def update_bank(upload_id: UUID, changes: BankEdit, x_session_token: SessionToken):
    with record_lock:
        record = session_record(upload_id, x_session_token)
        unit = next((u for u in record["units"] if u["id"] == str(changes.unit_id)), None)
        if unit is None:
            raise HTTPException(404, "Unit not found.")
        original = {q["id"]: q for q in unit["questions"]}
        ids = [str(q.id) for q in changes.questions]
        if len(set(ids)) != len(ids) or set(ids) != set(original):
            raise HTTPException(400, "The edit must contain each existing question exactly once. Disable questions to exclude them.")
        questions = []
        for edit in changes.questions:
            old = original[str(edit.id)]
            new = {**old, **edit.model_dump(mode="json", exclude_none=True)}
            new["text"] = normalize_legacy_symbols(new["text"])
            new["render_mode"] = "text"
            new["quality_issues"] = question_quality_issues(new["text"])
            if new["enabled"] and new["quality_issues"]:
                raise HTTPException(400, f"Question needs correction before it can be enabled: {new['quality_issues'][0]}")
            if edit.bloom != old["bloom"]:
                new["bloom_source"] = "reviewed"
            if edit.source_marks != old["source_marks"]:
                new["marks_source"] = "reviewed"
            questions.append(new)
        enabled_texts = [normalized_text(q["text"]) for q in questions if q["enabled"]]
        if len(enabled_texts) != len(set(enabled_texts)):
            raise HTTPException(400, "Enabled questions must have unique text. Disable or correct duplicates.")
        unit.update(name=changes.name, questions=questions)
        atomic_json(config.UPLOAD_DIR / str(upload_id) / "manifest.json", record)
        return public_session(record)


@router.get("/uploads/{upload_id}/assets/{asset_id}")
def asset(upload_id: UUID, asset_id: UUID, x_session_token: SessionToken):
    record = session_record(upload_id, x_session_token)
    name = str(asset_id) + ".png"
    if not any(name in q["assets"] + q.get("source_previews", []) + q.get("source_fragments", []) for u in record["units"] for q in u["questions"]):
        raise HTTPException(404, "Figure not found.")
    path = config.UPLOAD_DIR / str(upload_id) / "assets" / name
    if not path.is_file():
        raise HTTPException(404, "Figure not found.")
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "no-store"})


def save_paper(paper, session):
    pdf_id = str(uuid4())
    directory = config.OUT_DIR / pdf_id
    directory.mkdir(parents=True)
    try:
        # Snapshot figures and banks so saved papers remain reviewable after bank edits.
        assets = directory / "assets"
        assets.mkdir()
        source_dir = config.UPLOAD_DIR / session["upload_id"] / "assets"
        for name in {a for u in paper["units"] for alt in u["alternatives"] for q in alt["questions"] for a in q["assets"]}:
            shutil.copyfile(source_dir / name, assets / name)
        build_questionpaper_from_json(paper, directory / "paper.pdf", assets)
        with fitz.open(directory / "paper.pdf") as doc:
            page_count = len(doc)
        record = {"pdf_id": pdf_id, "paper": paper, "token_hash": session["token_hash"],
                  "expires_at": session["expires_at"], "session_snapshot": session, "page_count": page_count}
        atomic_json(directory / "paper.json", record)
        return {"status": "ok", "pdf_id": pdf_id, "paper": paper, "download_url": f"/download/{pdf_id}"}
    except Exception:
        shutil.rmtree(directory, ignore_errors=True)
        raise


@router.post("/generate")
def generate(request: GenerateRequest, x_session_token: SessionToken):
    session = session_record(request.upload_id, x_session_token)
    if not generation_slots.acquire(blocking=False):
        raise HTTPException(429, "The generator is busy. Please retry shortly.")
    try:
        paper = build_paper(request, session)
        return save_paper(paper, session)
    except ProviderError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        logger.exception("Paper generation failed")
        raise HTTPException(500, "The paper could not be created. Check the bank and retry.") from exc
    finally:
        generation_slots.release()


@router.get("/papers/{pdf_id}")
def get_paper(pdf_id: UUID, x_session_token: SessionToken):
    record = paper_record(pdf_id, x_session_token)
    return {"pdf_id": str(pdf_id), "paper": record["paper"],
            "units": record["session_snapshot"]["units"], "expires_at": record["expires_at"],
            "page_count": record.get("page_count", 1)}


@router.post("/papers/{pdf_id}/replace")
def replace_question(pdf_id: UUID, request: ReplaceRequest, x_session_token: SessionToken):
    record = paper_record(pdf_id, x_session_token)
    paper = copy.deepcopy(record["paper"])
    target = None
    for unit in paper["units"]:
        for alternative in unit["alternatives"]:
            for index, q in enumerate(alternative["questions"]):
                if q["id"] == str(request.question_id):
                    target = (unit, alternative, index, q)
    if target is None:
        raise HTTPException(404, "Selected question not found.")
    unit, alternative, index, previous = target
    bank = next(u for u in record["session_snapshot"]["units"] if u["id"] == unit["id"])
    replacement = next((q for q in eligible_questions(bank) if q["id"] == str(request.replacement_id)), None)
    if replacement is None:
        raise HTTPException(400, "Choose an enabled question from the same unit.")
    updated = copy.deepcopy(replacement)
    updated["marks"] = previous["marks"]
    updated["render_mode"] = "text"
    if not updated["include_figures"]:
        updated["assets"] = []
    alternative["questions"][index] = updated
    try:
        validate_paper(paper)
        refresh_warnings(paper)
        return save_paper(paper, record["session_snapshot"])
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/download/{pdf_id}")
def download(pdf_id: UUID, x_session_token: Annotated[str, Header(alias="X-Session-Token")] = "",
             expires: int = 0, signature: str = ""):
    if x_session_token:
        paper_record(pdf_id, x_session_token)
    elif expires and signature:
        signed_download_record(pdf_id, expires, signature)
    else:
        raise HTTPException(403, "A session token or valid download link is required.")
    path = config.OUT_DIR / str(pdf_id) / "paper.pdf"
    if not path.is_file():
        raise HTTPException(404, "PDF not found. Please regenerate the paper.")
    return FileResponse(path, media_type="application/pdf", filename=f"question_paper_{pdf_id}.pdf",
                        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


@router.get("/papers/{pdf_id}/download-link")
def download_link(pdf_id: UUID, x_session_token: SessionToken):
    record = paper_record(pdf_id, x_session_token)
    expires = min(int(time.time()) + 300, int(record["expires_at"]))
    signature = download_signature(record, pdf_id, expires)
    return {"url": f"/download/{pdf_id}?expires={expires}&signature={signature}"}


@router.get("/papers/{pdf_id}/pages/{page_number}")
def preview_page(pdf_id: UUID, page_number: int, x_session_token: SessionToken):
    paper_record(pdf_id, x_session_token)
    path = config.OUT_DIR / str(pdf_id) / "paper.pdf"
    if not path.is_file():
        raise HTTPException(404, "PDF not found. Please regenerate.")
    with fitz.open(path) as doc:
        if not 1 <= page_number <= len(doc):
            raise HTTPException(404, "Page not found.")
        png = doc[page_number-1].get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False).tobytes("png")
    return Response(png, media_type="image/png", headers={"Cache-Control": "no-store"})
