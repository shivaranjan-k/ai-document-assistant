from ollama import chat
from backend.rag.config import LLM_MODEL, FALLBACK_RESPONSE
from backend.rag.retrieval import _get_candidate_evidence
from backend.rag.grounding import _build_grounded_prompt, _is_fallback_answer
from backend.rag.sources import filter_supporting_sources
from backend.rag.conversation import is_context_dependent


def ask_question(query: str, messages: list, return_details: bool = False) -> dict:
    """
    Synchronous RAG pipeline:
    1. Shared retrieval & reranking & evidence validation
    2. Grounded LLM Generation
    3. Evidentiary Source Attribution
    """
    relevant_documents, relevant_metadatas, search_query, reranked_evidence, retrieved_sources = _get_candidate_evidence(query, messages)

    if not relevant_documents:
        res = {
            "answer": FALLBACK_RESPONSE,
            "sources": []
        }
        if return_details:
            res["reranked_evidence"] = reranked_evidence
            res["retrieved_sources"] = retrieved_sources
            res["search_query"] = search_query
        return res

    context = "\n\n".join(relevant_documents)
    history = "\n".join(
        f"{m['role']}: {m['content']}"
        for m in messages
    ) if messages else "None"

    resolved_q = search_query if (search_query != query and is_context_dependent(query, messages)) else query
    prompt = _build_grounded_prompt(context, history, resolved_q)

    response = chat(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.0}
    )

    answer = response.message.content.strip()

    if _is_fallback_answer(answer):
        res = {
            "answer": FALLBACK_RESPONSE,
            "sources": []
        }
        if return_details:
            res["reranked_evidence"] = reranked_evidence
            res["retrieved_sources"] = retrieved_sources
            res["search_query"] = search_query
        return res

    sources = filter_supporting_sources(answer, relevant_documents, relevant_metadatas)

    res = {
        "answer": answer,
        "sources": sources
    }
    if return_details:
        res["reranked_evidence"] = reranked_evidence
        res["retrieved_sources"] = retrieved_sources
        res["search_query"] = search_query

    return res


def stream_question(query: str, messages: list):
    """
    Streaming RAG pipeline:
    Uses identical shared core retrieval & evidence validation pipeline as ask_question.
    """
    relevant_documents, relevant_metadatas, search_query, reranked_evidence, retrieved_sources = _get_candidate_evidence(query, messages)

    if not relevant_documents:
        yield {
            "type": "answer",
            "content": FALLBACK_RESPONSE
        }
        yield {
            "type": "sources",
            "sources": []
        }
        return

    context = "\n\n".join(relevant_documents)
    history = "\n".join(
        f"{m['role']}: {m['content']}"
        for m in messages
    ) if messages else "None"

    resolved_q = search_query if (search_query != query and is_context_dependent(query, messages)) else query
    prompt = _build_grounded_prompt(context, history, resolved_q)

    response = chat(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.0},
        stream=True
    )

    full_answer = ""
    for chunk in response:
        content = chunk.message.content
        if content:
            full_answer += content
            yield {
                "type": "token",
                "content": content
            }

    full_answer_clean = full_answer.strip()

    if _is_fallback_answer(full_answer_clean):
        yield {
            "type": "sources",
            "sources": []
        }
        return

    sources = filter_supporting_sources(full_answer_clean, relevant_documents, relevant_metadatas)

    yield {
        "type": "sources",
        "sources": sources
    }
