"""Local records use unguessable IDs and separate session access tokens."""
import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import time
from pathlib import Path
from uuid import UUID, uuid4
from fastapi import HTTPException
from app.core import config

def secure_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", Path(name.replace(chr(92), "/")).name)[:180]

def atomic_json(path: Path, data: dict):
    temp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)

def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def new_token():
    token = secrets.token_urlsafe(32)
    return token, token_hash(token)

def read_record(path: Path, token: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise HTTPException(404, "This session or paper is missing or expired. Please upload again.")
    if not token or not hmac.compare_digest(data["token_hash"], token_hash(token)):
        raise HTTPException(403, "This session belongs to a different browser session.")
    if time.time() > data["expires_at"]:
        raise HTTPException(410, "This session has expired. Please upload again.")
    return data

def session_record(upload_id: UUID, token: str):
    return read_record(config.UPLOAD_DIR / str(upload_id) / "manifest.json", token)

def paper_record(pdf_id: UUID, token: str):
    return read_record(config.OUT_DIR / str(pdf_id) / "paper.json", token)

def public_session(record: dict):
    return {k: record[k] for k in ("upload_id", "units", "warnings", "expires_at")}

def cleanup_expired():
    """Remove managed UUID directories only; preserve the supplied sample files."""
    for base, filename in ((config.UPLOAD_DIR, "manifest.json"), (config.OUT_DIR, "paper.json")):
        if not base.exists():
            continue
        for directory in base.iterdir():
            try:
                UUID(directory.name)
                manifest = directory / filename
                if manifest.exists():
                    expired = json.loads(manifest.read_text())["expires_at"] < time.time()
                else:
                    expired = directory.stat().st_mtime < time.time() - 3600
                if directory.is_dir() and expired:
                    shutil.rmtree(directory)
            except (ValueError, KeyError, OSError):
                continue


def download_signature(record: dict, pdf_id: UUID, expires: int) -> str:
    payload = f"{pdf_id}:{expires}".encode()
    return hmac.new(bytes.fromhex(record['token_hash']), payload, hashlib.sha256).hexdigest()


def signed_download_record(pdf_id: UUID, expires: int, signature: str):
    path = config.OUT_DIR / str(pdf_id) / 'paper.json'
    try:
        record = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise HTTPException(404, 'Paper not found.')
    now = time.time()
    if expires < now or expires > now + 301 or record['expires_at'] < now:
        raise HTTPException(403, 'Download link expired. Use the Download PDF button to get a fresh link.')
    if not hmac.compare_digest(download_signature(record, pdf_id, expires), signature):
        raise HTTPException(403, 'Invalid download link.')
    return record
