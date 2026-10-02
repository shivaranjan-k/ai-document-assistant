import re
from backend.rag.grounding import _is_fallback_answer


def filter_supporting_sources(
    answer: str,
    relevant_documents: list,
    relevant_metadatas: list
) -> list:
    """
    Identifies which retrieved chunks actually contributed factual evidence to the final answer.
    Avoids citing chunks merely because they share a term with the answer.
    For fallback answers ('I don't have enough information to answer that.'), returns [].
    """
    if not answer or not relevant_documents or not relevant_metadatas:
        return []

    ans_clean = answer.strip()
    if _is_fallback_answer(ans_clean):
        return []

    stopwords = {
        "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
        "which", "this", "that", "these", "those", "then", "just", "so", "than",
        "such", "both", "through", "about", "for", "is", "are", "was", "were",
        "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "can", "could", "should", "would", "may", "might", "must", "will", "shall",
        "to", "of", "in", "on", "by", "at", "with", "from", "into", "during",
        "before", "after", "above", "below", "between", "under", "again", "further",
        "once", "here", "there", "when", "where", "why", "how", "all", "any",
        "each", "few", "more", "most", "other", "some", "no", "nor", "not",
        "only", "own", "same", "too", "very", "s", "t", "its", "it", "they",
        "them", "their", "user", "question", "answer", "pdf", "context"
    }

    answer_terms = [
        w for w in re.findall(r'\b[a-zA-Z0-9_\-\.]{3,}\b', ans_clean.lower())
        if w not in stopwords
    ]

    term_set = set(answer_terms)
    chunk_scores = []

    for doc, meta in zip(relevant_documents, relevant_metadatas):
        doc_lower = doc.lower() if isinstance(doc, str) else ""
        matched_terms = {t for t in term_set if t in doc_lower}
        chunk_scores.append((len(matched_terms), doc, meta))

    max_score = max(score for score, _, _ in chunk_scores) if chunk_scores else 0
    sources = []
    shown_sources = set()

    for score, doc, meta in chunk_scores:
        meta_dict = meta if isinstance(meta, dict) else {}
        source_name = meta_dict.get("source", "")
        page_num = meta_dict.get("page", 1)
        source_key = (source_name, page_num)

        is_contributing = (score >= 2 and score >= max_score * 0.3) or (max_score < 2 and score == max_score and score > 0)

        if is_contributing and source_key not in shown_sources:
            sources.append({
                "source": source_name,
                "page": page_num
            })
            shown_sources.add(source_key)

    if not sources and relevant_metadatas:
        first_meta = relevant_metadatas[0] if isinstance(relevant_metadatas[0], dict) else {}
        source_name = first_meta.get("source", "")
        if source_name:
            sources.append({
                "source": source_name,
                "page": first_meta.get("page", 1)
            })

    return sources
