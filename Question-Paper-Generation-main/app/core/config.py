"""Configuration is independent of the terminal's working directory."""
import os
from pathlib import Path
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", str(BASE_DIR / "storage"))).resolve()
UPLOAD_DIR = STORAGE_DIR / "sessions"
OUT_DIR = STORAGE_DIR / "papers"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_TIMEOUT = float(os.getenv("GEMINI_TIMEOUT", "45"))
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_FILES = 12
MAX_PAGES = 100
MAX_QUESTIONS = 500
RETENTION_HOURS = int(os.getenv("RETENTION_HOURS", "168"))
CORS_ORIGINS = [s.strip() for s in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if s.strip()]
_frontend_dist = os.getenv("FRONTEND_DIST", "").strip()
FRONTEND_DIST = Path(_frontend_dist).resolve() if _frontend_dist else None
def create_storage_directories():
    for directory in (UPLOAD_DIR, OUT_DIR):
        directory.mkdir(parents=True, exist_ok=True)

# Local printed-text OCR. One shared budget covers every PDF in an upload.
TESSERACT_CMD = os.getenv('TESSERACT_CMD', 'tesseract')
OCR_LANGUAGE = os.getenv('OCR_LANGUAGE', 'eng')
OCR_MAX_PAGES = 20
OCR_PAGE_TIMEOUT = 20
OCR_UPLOAD_TIMEOUT = 90
OCR_MAX_PIXELS = 12_000_000
