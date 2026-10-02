import sys
from pathlib import Path

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHROMA_PATH = str(BASE_DIR / "chroma_db")
DOCUMENTS_FOLDER = BASE_DIR / "documents"

COLLECTION_NAME = "pdf_knowledge"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
LLM_MODEL = "llama3.2:3b"

TOP_K = 3
RERANK_THRESHOLD = -7.0
FALLBACK_RESPONSE = "I don't have enough information to answer that."
