import re
from backend.rag.config import FALLBACK_RESPONSE
from backend.rag.conversation import is_context_dependent


def _is_fallback_answer(text: str) -> bool:
    if not text:
        return True
    t = text.lower().strip()
    fallback_signals = [
        "don't have enough information",
        "do not have enough information",
        "insufficient information",
        "does not mention",
        "does not explicitly mention",
        "not explicitly mention",
        "not mentioned",
        "no mention",
        "not mention",
        "no information",
        "not specified",
        "not provided",
        "cannot be answered",
        "no evidence",
        "not explicitly state",
        "not state",
        "does not state"
    ]
    return any(sig in t for sig in fallback_signals) or t == FALLBACK_RESPONSE.lower()


def validate_and_filter_evidence(
    query: str,
    search_query: str,
    candidate_documents: list,
    candidate_metadatas: list,
    messages: list = None
) -> tuple:
    """
    Document-agnostic evidence validation layer that runs between reranking and LLM generation.
    Determines whether candidate chunks actually support the query's target subject/intent.
    Returns (validated_documents, validated_metadatas).
    If evidence is absent, weak, unrelated, cross-document unsupported, or unresolvable, returns ([], []).
    """
    if not candidate_documents:
        return [], []

    # 1. Unresolvable Pronouns / Context Dependency Check
    if not messages and is_context_dependent(query, messages):
        return [], []

    coref_pronouns = {"it", "its", "this", "that", "these", "those", "they", "them", "their", "he", "him", "his", "she", "her"}
    search_words = re.findall(r'\b[a-zA-Z0-9_\-\+\#]+\b', search_query.lower())
    search_word_set = set(search_words)

    if not messages and bool(search_word_set & coref_pronouns):
        substantive_tokens = [
            w for w in search_words
            if w not in coref_pronouns and w not in {
                "what", "how", "why", "where", "when", "which", "is", "are", "was", "were",
                "do", "does", "did", "use", "used", "uses", "using", "the", "a", "an", "language", "system"
            }
        ]
        if not substantive_tokens:
            return [], []

    # 2. Cross-Document / Entity Relationship Verification
    stopwords = {
        "what", "is", "are", "was", "were", "do", "does", "did", "can", "could", "would",
        "should", "how", "why", "where", "when", "which", "give", "show", "tell", "me", "us",
        "an", "a", "the", "of", "for", "in", "on", "to", "with", "about", "example", "examples",
        "explain", "simply", "advantage", "advantages", "disadvantage", "disadvantages",
        "detail", "details", "work", "works", "working", "use", "used", "uses", "usage"
    }

    rel_match = re.search(
        r'\b(?:does|is|has|did|can|will)\s+([a-zA-Z0-9_\-\+\#\s]+?)\s+(?:use|uses|have|has|support|supports|contain|contains|include|includes|with|using)\s+([a-zA-Z0-9_\-\+\#\s]+)\b',
        search_query,
        re.IGNORECASE
    )
    if rel_match:
        entity_a = rel_match.group(1).strip().lower()
        entity_b = rel_match.group(2).strip().lower()

        a_tokens = [w for w in entity_a.split() if w not in stopwords]
        b_tokens = [w for w in entity_b.split() if w not in stopwords]

        if a_tokens and b_tokens:
            supported = False
            for doc in candidate_documents:
                doc_l = doc.lower() if isinstance(doc, str) else ""
                has_a = any(t in doc_l for t in a_tokens)
                has_b = any(t in doc_l for t in b_tokens)
                if has_a and has_b:
                    supported = True
                    break

            if not supported:
                sources = {meta.get("source", "") if isinstance(meta, dict) else "" for meta in candidate_metadatas}
                if len(sources) > 1 or not sources:
                    return [], []

    valid_docs = [doc for doc in candidate_documents if isinstance(doc, str) and doc.strip()]
    valid_metas = [meta if isinstance(meta, dict) else {} for meta in candidate_metadatas[:len(valid_docs)]]

    return valid_docs, valid_metas


def _build_grounded_prompt(context: str, history: str, resolved_q: str) -> str:
    return f"""You are a helpful, factual PDF document assistant.

Your task is to answer the user's question based ONLY on the PDF CONTEXT provided below.

PDF CONTEXT:
{context}

PREVIOUS CONVERSATION:
{history}

USER QUESTION:
{resolved_q}

STRICT GROUNDING & EVIDENCE RULES:
1. Answer ONLY using explicit facts directly stated in the PDF CONTEXT. Do not add general programming knowledge or external domain knowledge that is absent from the PDF context.
2. PREVIOUS CONVERSATION is provided solely to resolve references. Never use previous conversation as factual evidence.
3. ENTITY & FACTUAL RELATIONSHIP ACCURACY:
   - Match properties, features, and facts ONLY to the specific heading, section, or entity under which they are explicitly stated.
   - Do NOT attribute properties from one document or entity to another.
   - Never reverse the subject or object of a factual statement from the PDF.
   - Preserve factual relationships exactly when paraphrasing. For example, if the PDF states "the subclass inherits the accessible members of the superclass", the answer must NOT say "the superclass inherits the accessible members of the subclass" or "the superclass inherits the accessible members of the superclass".
   - When the PDF directly states the relevant information, prefer quoting or closely preserving the PDF wording instead of freely paraphrasing it.
4. ADVERSARIAL PREMISE REJECTION:
   - If a question contains an unverified premise, do NOT accept the premise as true.
5. CONTRADICTION & AMBIGUITY HANDLING:
   - Check if the PDF CONTEXT contains contradictory or conflicting facts for the question.
   - If contradictory or conflicting facts exist in the context for the same entity or system, you MUST explicitly state BOTH conflicting statements/items OR respond with EXACTLY: "I don't have enough information to answer that."
   - UNRESOLVED AMBIGUOUS REFERENCES: If the question uses an ambiguous reference like 'it', 'this', or 'which one' and the PDF CONTEXT describes multiple entities without specifying which one is being asked about, respond with EXACTLY:
     "I don't have enough information to answer that."
6. ABSENCE OF EVIDENCE & REQUESTED ASPECT ACCURACY:
   - If the PDF CONTEXT does NOT explicitly contain positive evidence to support the answer, respond with EXACTLY:
     "I don't have enough information to answer that." Do NOT write custom negative statements like "The PDF does not mention...".
   - Do not infer advantages merely because the user asks "What are the advantages?". If the PDF context does not explicitly state advantages, do not invent advantages.
   - If the PDF provides related information but does not explicitly answer the user's requested aspect, respond with EXACTLY:
     "I don't have enough information to answer that."
7. FORMATTING:
   - Answer directly and concisely without repeating the prompt or adding meta-commentary like "Based on the PDF...".
"""
