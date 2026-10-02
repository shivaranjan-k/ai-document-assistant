import re
from ollama import chat
from backend.rag.config import LLM_MODEL


def is_context_dependent(query: str, messages: list) -> bool:
    """
    Determines whether a query requires conversational context based on generic
    linguistic structures (pronouns, coreference terms, elliptical follow-ups,
    subjectless imperative or property requests, or selection phrases) while
    protecting complete standalone questions containing their own explicit topic.
    """
    if not messages:
        return False

    q_clean = query.strip()
    q_lower = q_clean.lower()
    words = re.findall(r'\b[a-zA-Z0-9_\-\+\#]+\b', q_lower)
    if not words:
        return False

    word_set = set(words)
    first_word = words[0]

    # 1. Coreference pronouns indicating explicit dependency on conversation
    coref_pronouns = {"it", "its", "this", "that", "these", "those", "they", "them", "their", "he", "him", "his", "she", "her", "hers"}
    if bool(word_set & coref_pronouns):
        return True

    # 2. Comparative / selection references
    selection_patterns = [
        r"\bwhich\s+(?:one|of\s+them|of\s+those|of\s+these|of\s+the\s+\w+|option|system|model|tool|project|document)\b",
        r"\bbetween\s+(?:them|both|these|those)\b",
        r"\b(?:the\s+former|the\s+latter|the\s+first\s+one|the\s+second\s+one|the\s+other\s+one)\b",
        r"\b(?:as\s+mentioned|you\s+mentioned|mentioned\s+earlier|mentioned\s+above)\b",
        r"\b(?:what\s+else|anything\s+else)\b"
    ]
    for pattern in selection_patterns:
        if re.search(pattern, q_lower):
            return True

    # Generic relational/attribute nouns that signify an aspect of a topic
    relational_nouns = {
        "example", "examples", "sample", "samples", "syntax", "code", "implementation",
        "detail", "details", "illustration", "steps", "usage", "advantage", "advantages",
        "disadvantage", "disadvantages", "pro", "pros", "con", "cons", "benefit", "benefits",
        "drawback", "drawbacks", "limitation", "limitations", "feature", "features", "difference",
        "differences", "usecase", "usecases", "case", "cases", "purpose", "mechanism", "definition",
        "working", "workings", "architecture", "concept", "components", "part", "parts"
    }
    adverbial_modifiers = {"further", "more", "again", "simply", "briefly", "detail", "deeply"}
    filler_and_polite = {"can", "could", "would", "you", "please", "me", "us", "a", "an", "the", "some", "any"}
    prepositions = {"of", "for", "about", "regarding", "between", "in", "to", "with"}
    manner_or_filler = {"detail", "details", "depth", "brief", "short", "simple", "general", "terms"}

    # Check for explicit prepositional complement indicating a standalone subject (e.g., 'of inheritance', 'about TCP')
    has_explicit_complement = False
    comp_matches = re.findall(r'\b(?:of|about|regarding|between|for|in)\s+([a-zA-Z0-9_\-\+\#]+(?:\s+[a-zA-Z0-9_\-\+\#]+)*)', q_lower)
    for match in comp_matches:
        comp_tokens = set(match.split()) - filler_and_polite - manner_or_filler - coref_pronouns - relational_nouns
        if comp_tokens:
            has_explicit_complement = True
            break

    # 3. Subjectless imperative requests (e.g. "Give me an example.", "give me a examplle", "Explain simply.")
    imperative_verbs = {
        "give", "show", "provide", "share", "explain", "elaborate", "describe",
        "illustrate", "clarify", "list", "tell", "expand", "continue"
    }
    is_imperative_start = first_word in imperative_verbs or (
        len(words) > 1 and first_word in {"can", "could", "would", "please"} and any(w in imperative_verbs for w in words[1:3])
    )

    if is_imperative_start:
        if len(words) <= 5 and not has_explicit_complement:
            return True

        verb_idx = -1
        for i, w in enumerate(words):
            if w in imperative_verbs:
                verb_idx = i
                break
        post_verb_tokens = []
        for w in words[verb_idx + 1:]:
            if w in prepositions or w in adverbial_modifiers:
                break
            if w not in filler_and_polite and w not in coref_pronouns:
                post_verb_tokens.append(w)
        substantive_objects = [w for w in post_verb_tokens if w not in relational_nouns and w not in manner_or_filler]

        if substantive_objects or has_explicit_complement:
            return False
        return True

    # 4. Subjectless elliptical property questions (e.g., "What are the advantages?", "How does it work?")
    is_question_start = first_word in {"what", "how", "why", "where", "when", "which"}
    if is_question_start:
        if bool(word_set & relational_nouns) and not has_explicit_complement:
            return True
        if len(words) <= 5 and any(w in word_set for w in {"work", "useful", "used", "workings", "help", "happen"}):
            if not has_explicit_complement and not any(w not in filler_and_polite and w not in relational_nouns and w not in {"how", "does", "why", "is", "work", "useful", "used"} for w in words):
                return True

    # 5. Short utterances (<= 4 words)
    if len(words) <= 4:
        if len(words) in [3, 4] and first_word in {"what", "who", "where", "which"} and words[1] in {"is", "are", "was", "were"}:
            subject_word = words[2]
            if subject_word not in coref_pronouns and subject_word not in relational_nouns:
                return False
        if len(words) == 2 and first_word in imperative_verbs and words[1] not in relational_nouns and words[1] not in coref_pronouns and words[1] not in manner_or_filler:
            return False
        if len(words) <= 2 or any(w in word_set for w in {"more", "another", "else", "simply", "briefly", "examples"}):
            return True

    return False


def extract_active_topic(messages: list) -> str:
    """
    Extracts the active topic from recent user messages, searching from newest to oldest.
    """
    if not messages:
        return ""

    user_msgs = [m['content'].strip() for m in messages if m['role'] == 'user']
    if not user_msgs:
        return ""

    non_topics = {"give me an example", "give me a example", "give me a examplle", "explain it simply", "what are the advantages", "how does it work", "tell me more"}

    for msg in reversed(user_msgs):
        m_clean = msg.strip()
        m_lower = m_clean.lower().rstrip('?.!')
        words = re.findall(r'\b[a-zA-Z0-9_\-\+\#]+\b', m_lower)
        if not words:
            continue

        match = re.search(r'\b(?:what|who|how|why)\s+(?:is|are|was|were|about)\s+([a-zA-Z0-9_\-\+\#\s]+)', m_clean, re.IGNORECASE)
        if match:
            topic_candidate = match.group(1).strip().rstrip('?.!')
            topic_words = set(topic_candidate.lower().split())
            if not topic_words.intersection(non_topics):
                return topic_candidate

        if words[0] in {"explain", "describe", "discuss"} and len(words) > 1:
            topic_candidate = " ".join(words[1:])
            if topic_candidate not in non_topics:
                return topic_candidate

        if 1 <= len(words) <= 4 and not any(w in m_lower for w in ["what", "how", "why", "where", "when", "give", "show", "tell"]):
            if m_lower not in non_topics:
                return m_clean

    return user_msgs[-1] if user_msgs else ""


def rewrite_query(query: str, messages: list) -> str:
    """
    Rewrites a context-dependent user follow-up into a complete, standalone retrieval query
    using a strict Recency-First resolution strategy over the conversation history.
    This step runs BEFORE vector retrieval.
    """
    if not is_context_dependent(query, messages):
        return query

    active_topic = extract_active_topic(messages)
    q_clean = query.strip()
    q_lower = q_clean.lower().rstrip('?.!')

    # Deterministic resolution for simple elliptical follow-ups when active topic is present
    if active_topic:
        if any(tok in q_lower for tok in ["example", "examplle", "exampel", "sample", "illustration"]):
            return f"{active_topic} example"
        if q_lower in ["explain it simply", "explain it simply.", "explain simply", "explain simply."]:
            return f"Explain {active_topic} simply"
        if q_lower in ["what are the advantages", "what are the advantages?", "advantages", "what are its advantages"]:
            return f"What are the advantages of {active_topic}?"
        if q_lower in ["how does it work", "how does it work?", "how it works", "mechanism"]:
            return f"How does {active_topic} work?"

    recent = messages[-6:] if messages else []
    history_lines = []
    for m in recent:
        role = "User" if m['role'] == 'user' else "Assistant"
        content = m['content'] if m['role'] == 'user' else (m['content'][:120] + "..." if len(m['content']) > 120 else m['content'])
        history_lines.append(f"{role}: {content}")
    history_text = "\n".join(history_lines) if history_lines else "None"

    prompt = f"""You are a search query rewriter for a conversational document retrieval engine.

Your task is to rewrite the user's follow-up question into ONE complete, standalone search query by combining:
[CURRENT USER INTENT / PREDICATE] + [ACTIVE TOPIC FROM RECENT CONVERSATION]

CRITICAL RULES:
1. RECENCY-FIRST TOPIC RESOLUTION:
   - Active Topic from recent conversation: '{active_topic}'.
   - If the user switched topics, you MUST resolve the follow-up using the LATEST active topic ('{active_topic}'), NOT any older topic.
2. PRESERVE INTENT & PREDICATE:
   - Keep what the user is asking for (e.g., an example, advantages, explanation, syntax, mechanics, usage).
   - Formulate a clean standalone retrieval query applying that exact request to the active topic (e.g., '{active_topic} example', 'What are the advantages of {active_topic}?').
3. STANDALONE OVERRIDE:
   - If the user question introduces an explicit new subject, treat it as a standalone query.
4. NO ANSWERING & NO EXTERNAL FACTS:
   - Output ONLY the standalone search query. Never answer the question or invent entities.
5. OUTPUT FORMAT:
   - Return ONLY the standalone search query string with no preamble or quotes.

CONVERSATION HISTORY:
{history_text}

USER FOLLOW-UP QUESTION:
{query}

Standalone search query:"""

    try:
        response = chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.0}
        )

        raw_res = response.message.content if response and response.message else None
        if not isinstance(raw_res, str):
            rewritten = query
        else:
            rewritten = raw_res.strip().strip('"').strip("'")
            if not rewritten or rewritten.lower() in ["none", "no response", "(no response)"]:
                rewritten = query
    except Exception as e:
        print(f"Query rewrite error: {e}")
        rewritten = query

    if not isinstance(rewritten, str) or not rewritten.strip():
        rewritten = query

    print("\n" + "=" * 60)
    print("🔄 CONVERSATIONAL QUERY RESOLUTION (PRE-RETRIEVAL)")
    print("=" * 60)
    print(f"Original query:  {query}")
    print(f"Resolved query:  {rewritten}")
    print("=" * 60 + "\n")

    return rewritten


def characterize_query_intent(query: str, search_query: str) -> str:
    """
    Determines whether a query asks for a broad conceptual summary, topic explanation,
    category list, architectural overview, or multi-concept description versus a narrow
    single-concept/fact query based on generic linguistic structures.
    Returns 'broad_conceptual' or 'narrow_specific'.
    """
    q_lower = (query + " " + search_query).lower()
    words = set(re.findall(r'\b[a-zA-Z0-9_\-\+\#]+\b', q_lower))

    category_indicators = {
        "concept", "concepts", "overview", "architecture", "component", "components",
        "feature", "features", "principle", "principles", "pillar", "pillars",
        "fundamental", "fundamentals", "basic", "basics", "structure", "system",
        "summary", "summarize", "list", "all", "different", "various", "main", "key",
        "types", "categories", "aspects", "elements", "parts"
    }

    if bool(words & category_indicators):
        return "broad_conceptual"

    if any(q_lower.startswith(prefix) for prefix in ["explain ", "overview ", "summarize ", "describe "]):
        relational_property_terms = {"syntax", "author", "creator", "date", "year", "formula", "equation", "price", "cost", "salary", "address", "phone"}
        if not bool(words & relational_property_terms):
            return "broad_conceptual"

    return "narrow_specific"
