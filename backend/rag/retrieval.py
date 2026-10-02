from pathlib import Path
from backend.rag.config import TOP_K, RERANK_THRESHOLD
from backend.rag.embeddings import embedding_model
from backend.rag.vector_store import collection
from backend.rag.reranker import reranker
from backend.rag.conversation import rewrite_query, characterize_query_intent
from backend.rag.grounding import validate_and_filter_evidence


def _get_candidate_evidence(query: str, messages: list) -> tuple:
    """
    Shared candidate retrieval, reranking, evidence selection, and evidence validation.
    Returns:
    (relevant_documents, relevant_metadatas, search_query, reranked_evidence, retrieved_sources)
    """
    search_query = rewrite_query(query, messages)

    query_embedding = embedding_model.encode(search_query).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=15,
        include=["documents", "distances", "metadatas"]
    )

    documents = results["documents"][0] if results.get("documents") else []
    metadatas = results["metadatas"][0] if results.get("metadatas") else []
    distances = results["distances"][0] if results.get("distances") else []

    pairs = []
    for doc, meta in zip(documents, metadatas):
        source_name = meta.get("source", "") if isinstance(meta, dict) else ""
        clean_title = Path(source_name).stem.replace("_", " ").replace("-", " ")
        rerank_text = f"Document: {clean_title}\n{doc}"
        pairs.append([search_query, rerank_text])

    scores = reranker.predict(pairs) if pairs else []

    ranked_results = sorted(
        zip(scores, documents, metadatas, distances),
        key=lambda x: x[0],
        reverse=True
    ) if pairs else []

    reranked_evidence = [
        {
            "score": round(float(score), 4),
            "source": meta.get("source") if isinstance(meta, dict) else "",
            "page": meta.get("page") if isinstance(meta, dict) else 1,
            "status": "PASS" if score >= RERANK_THRESHOLD else "FAIL",
            "snippet": doc[:120].replace("\n", " ").strip()
        }
        for score, doc, meta, dist in ranked_results[:TOP_K]
    ]
    retrieved_sources = [
        {"source": meta.get("source") if isinstance(meta, dict) else "", "page": meta.get("page") if isinstance(meta, dict) else 1}
        for meta in metadatas[:TOP_K]
    ]

    intent = characterize_query_intent(query, search_query)
    candidate_k = 6 if intent == "broad_conceptual" else TOP_K

    candidate_documents = []
    candidate_metadatas = []
    for score, doc, meta, dist in ranked_results:
        if score >= RERANK_THRESHOLD:
            candidate_documents.append(doc)
            candidate_metadatas.append(meta)
            if len(candidate_documents) == candidate_k:
                break

    relevant_documents, relevant_metadatas = validate_and_filter_evidence(
        query,
        search_query,
        candidate_documents,
        candidate_metadatas,
        messages
    )

    return relevant_documents, relevant_metadatas, search_query, reranked_evidence, retrieved_sources
