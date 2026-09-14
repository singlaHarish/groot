import re

def extract_keywords(query: str) -> list[str]:
    """
    Extracts meaningful keywords from a query for use in re-ranking.
    Strips common stop words and instruction verbs, keeping domain terms.
    """
    stop_words = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "on", "at", "by", "for", "with", "about",
        "against", "between", "through", "during", "before", "after", "above",
        "below", "from", "up", "down", "out", "off", "over", "under", "again",
        "then", "once", "and", "but", "or", "nor", "so", "yet", "both",
        "either", "neither", "not", "if", "when", "while", "how", "what",
        "which", "who", "whom", "whose", "that", "this", "these", "those",
        "i", "me", "my", "we", "our", "you", "your", "he", "she", "it",
        "his", "her", "its", "they", "their", "them",
        "summarize", "summarise", "explain", "describe", "list", "give",
        "tell", "provide", "find", "show", "get", "extract", "identify",
    }
    words = re.findall(r"[a-z0-9]+", query.lower())
    return [w for w in words if w not in stop_words and len(w) > 2]

def expand_query(query: str) -> list[str]:
    """
    Generates sub-queries from the original query to improve retrieval recall.
    """
    query_lower = query.lower().strip()

    instruction_prefixes = [
        "summarize", "summarise", "explain", "describe", "list",
        "what are", "what is", "tell me about", "give me", "provide",
        "extract", "find", "identify", "outline",
    ]

    core_topic = query_lower
    for prefix in instruction_prefixes:
        if core_topic.startswith(prefix):
            core_topic = core_topic[len(prefix):].strip().lstrip("the ").strip()
            break

    sub_queries = []

    if core_topic and core_topic != query_lower and len(core_topic) > 3:
        sub_queries.append(core_topic)

    conditional_pattern = re.compile(
        r'\b(when|if|while|during|after|before|unless|until)\b(.{3,60})',
        re.IGNORECASE
    )
    for match in conditional_pattern.finditer(query_lower):
        clause = match.group(0).strip()
        if clause not in sub_queries:
            sub_queries.append(clause)
        noun_phrase = match.group(2).strip()
        if noun_phrase and noun_phrase not in sub_queries:
            sub_queries.append(noun_phrase)

    keywords = extract_keywords(query)
    if keywords:
        keyword_query = " ".join(keywords[:3])
        if keyword_query not in sub_queries and keyword_query != core_topic:
            sub_queries.append(keyword_query)

    return sub_queries
