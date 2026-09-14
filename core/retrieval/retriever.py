import numpy as np
from core.vectorstore.embeddings import get_embedding_model
from core.retrieval.query_expansion import expand_query, extract_keywords

def search_chunks(query: str, index, chunks: list[str], api_key: str = None, top_k: int = 3) -> list[str]:
    """
    Embeds the query locally, searches the FAISS index, and returns top_k chunks.
    Uses query expansion and keyword-boosted re-ranking.
    """
    embedding_model = get_embedding_model()
    if embedding_model is None:
        return []

    sub_queries = expand_query(query)
    all_queries = [query] + sub_queries

    seen_indices = set()
    candidate_chunks = []

    for q in all_queries:
        query_vector = embedding_model.encode([q])
        query_vector = np.array(query_vector, dtype=np.float32)

        fetch_k = min(top_k * 5, len(chunks))
        distances, indices = index.search(query_vector, fetch_k)

        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(chunks) and idx not in seen_indices:
                seen_indices.add(idx)
                candidate_chunks.append((dist, idx, chunks[idx]))

    query_keywords = extract_keywords(query)
    KEYWORD_BONUS = 0.08

    def adjusted_distance(dist, chunk_text):
        chunk_lower = chunk_text.lower()
        matched = sum(1 for kw in query_keywords if kw in chunk_lower)
        return dist - (matched * KEYWORD_BONUS)

    candidate_chunks.sort(key=lambda x: adjusted_distance(x[0], x[2]))

    SIMILARITY_THRESHOLD = 2.0
    filtered = [chunk for dist, idx, chunk in candidate_chunks if dist <= SIMILARITY_THRESHOLD]

    if not filtered:
        filtered = [chunk for _, _, chunk in candidate_chunks[:top_k]]

    return filtered[:top_k]
