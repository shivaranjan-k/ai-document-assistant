"""
Compatibility and orchestration layer for the RAG engine.
Re-exports public interfaces from backend.rag modules to preserve backward compatibility.
"""

from backend.rag.config import (
    BASE_DIR,
    CHROMA_PATH,
    DOCUMENTS_FOLDER,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    RERANKER_MODEL,
    LLM_MODEL,
    TOP_K,
    RERANK_THRESHOLD,
    FALLBACK_RESPONSE
)
from backend.rag.embeddings import embedding_model
from backend.rag.vector_store import client, collection
from backend.rag.reranker import reranker
from backend.rag.conversation import (
    is_context_dependent,
    extract_active_topic,
    rewrite_query,
    characterize_query_intent
)
from backend.rag.grounding import validate_and_filter_evidence, _is_fallback_answer, _build_grounded_prompt
from backend.rag.sources import filter_supporting_sources
from backend.rag.retrieval import _get_candidate_evidence
from backend.rag.generation import ask_question, stream_question
from backend.rag.ingestion import create_chunks, ingest_pdf

__all__ = [
    "ask_question",
    "stream_question",
    "ingest_pdf",
    "create_chunks",
    "collection",
    "client",
    "embedding_model",
    "reranker",
    "rewrite_query",
    "is_context_dependent",
    "extract_active_topic",
    "characterize_query_intent",
    "validate_and_filter_evidence",
    "filter_supporting_sources",
    "BASE_DIR",
    "CHROMA_PATH",
    "DOCUMENTS_FOLDER",
    "COLLECTION_NAME",
    "EMBEDDING_MODEL",
    "RERANKER_MODEL",
    "LLM_MODEL",
    "TOP_K",
    "RERANK_THRESHOLD",
    "FALLBACK_RESPONSE"
]