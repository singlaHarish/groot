from sentence_transformers import SentenceTransformer
from core.config import configure_environment

_embedding_model_cache = None

def get_embedding_model():
    """Load embedding model with thread-safe caching."""
    global _embedding_model_cache
    
    if _embedding_model_cache is not None:
        return _embedding_model_cache
    
    try:
        configure_environment()
        _embedding_model_cache = SentenceTransformer('all-MiniLM-L6-v2')
        return _embedding_model_cache
    except Exception:
        return None
