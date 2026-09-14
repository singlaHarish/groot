"""
Unit test for Groot Core package modules.
"""

import sys
sys.path.insert(0, '.')

from core.ingestion.parser import extract_text_from_pdf
from core.ingestion.chunker import chunk_text, count_tokens
from core.vectorstore.embeddings import get_embedding_model
from core.vectorstore.faiss_store import build_faiss_index
from core.retrieval.query_expansion import expand_query, extract_keywords
from core.retrieval.retriever import search_chunks
from core.evaluation.quality import compute_response_quality

def test_core_pipeline():
    sample_text = (
        "Groot is an AI document context optimizer. "
        "It retrieves relevant document sections using vector search and query expansion. "
        "This reduces token usage and LLM API costs significantly."
    )
    
    # 1. Test Ingestion
    chunks = chunk_text(sample_text, chunk_size=50, chunk_overlap=10)
    assert len(chunks) > 0, "Chunking failed"
    token_count = count_tokens(sample_text)
    assert token_count > 0, "Token counting failed"
    
    # 2. Test Retrieval & Query Expansion
    keywords = extract_keywords("How does Groot optimize AI document context?")
    assert "groot" in keywords or "optimize" in keywords
    sub_queries = expand_query("explain how groot works when source file is open")
    assert len(sub_queries) > 0
    
    # 3. Test Vector Store & Search
    index, embeddings = build_faiss_index(chunks, show_progress=False)
    results = search_chunks("context optimizer", index, chunks, top_k=2)
    assert len(results) > 0, "Vector search returned no results"
    
    # 4. Test Evaluation
    quality = compute_response_quality(sample_text, sample_text)
    assert quality["f1"] > 0.8, "Quality metric evaluation failed"
    
    print("✅ All Groot core package unit tests passed!")

if __name__ == "__main__":
    test_core_pipeline()
