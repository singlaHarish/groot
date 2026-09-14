"""
Facade module for backward compatibility. Re-exports functions and classes from core.
"""

from core.ingestion.parser import extract_text_from_pdf
from core.ingestion.chunker import chunk_text, count_tokens, get_encoder
from core.vectorstore.embeddings import get_embedding_model
from core.vectorstore.faiss_store import build_faiss_index
from core.vectorstore.persistent_store import load_persistent_index, save_persistent_index, get_doc_hash
from core.retrieval.query_expansion import expand_query as _expand_query, extract_keywords as _extract_keywords
from core.retrieval.retriever import search_chunks
from core.evaluation.quality import compute_response_quality
from core.generation.gemini import generate_gemini_response, generate_gemini_vertex
from core.services.document_processor import DocumentProcessorThread
