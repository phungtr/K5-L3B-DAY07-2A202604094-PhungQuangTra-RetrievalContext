"""Đường dẫn, biến môi trường và hằng số dùng chung."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
CHUNKS_PATH = DATA_DIR / "chunks.json"
INDEX_INFO_PATH = DATA_DIR / "index_info.json"
MANIFEST_PATH = DATA_DIR / "manifest.json"
QUESTIONS_PATH = DATA_DIR / "questions.json"          # câu có đáp án (schema starter, có gold)
UNANSWERABLE_PATH = DATA_DIR / "unanswerable.json"    # câu thiếu evidence
ENV_PATH = ROOT / ".env"

# Repo Day 6 nằm cạnh repo này; chỉ dùng để đọc PDF gốc khi đối chiếu evidence.
DAY6_ROOT = ROOT.parent / "K5-L3B-DAY06-PhungQuangTra-2A202604094-DataIngestion"

# Day 6 chọn cấu hình C = chunk/vector của B + lọc edition lúc truy vấn. Day 7 dùng đúng các dòng strategy B.
DAY6_STRATEGY = "B"
EMBEDDING_DIMENSIONS = 1536


def utf8_console() -> None:
    """Console Windows mặc định cp1252: in tiếng Việt sẽ lỗi nếu không đổi sang UTF-8."""
    import sys
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def load_env() -> None:
    from dotenv import load_dotenv
    utf8_console()
    load_dotenv(ENV_PATH)


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Thiếu {name}; copy .env.example thành .env và điền giá trị")
    return value
