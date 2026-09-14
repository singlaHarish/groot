import os
import json
import hashlib
import faiss
from typing import Optional, Dict, Any, Tuple

CACHE_DIR = os.path.join(os.getcwd(), ".groot_cache")
METADATA_FILE = os.path.join(CACHE_DIR, "metadata.json")
INDEXES_DIR = os.path.join(CACHE_DIR, "indexes")

def _ensure_cache_dirs():
    """Ensure cache directories exist."""
    os.makedirs(INDEXES_DIR, exist_ok=True)
    if not os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

def get_doc_hash(pdf_path: str, chunk_size: int = 500, chunk_overlap: int = 100) -> str:
    """
    Computes SHA-256 fingerprint from pdf path, modified time, size, and chunking parameters.
    """
    abs_path = os.path.abspath(pdf_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"File not found: {abs_path}")
    
    stat = os.stat(abs_path)
    key_string = f"{abs_path}:{stat.st_mtime}:{stat.st_size}:{chunk_size}:{chunk_overlap}"
    return hashlib.sha256(key_string.encode("utf-8")).hexdigest()

def load_persistent_index(pdf_path: str, chunk_size: int = 500, chunk_overlap: int = 100) -> Optional[Dict[str, Any]]:
    """
    Loads persistent FAISS index and metadata if cache exists and is valid.
    """
    try:
        _ensure_cache_dirs()
        doc_hash = get_doc_hash(pdf_path, chunk_size, chunk_overlap)
        index_file = os.path.join(INDEXES_DIR, f"{doc_hash}.index")
        
        if not os.path.exists(index_file):
            return None
        
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            all_metadata = json.load(f)
            
        if doc_hash not in all_metadata:
            return None
            
        metadata = all_metadata[doc_hash]
        index = faiss.read_index(index_file)
        
        return {
            "full_text": metadata["full_text"],
            "chunks": metadata["chunks"],
            "index": index,
            "chunk_size": metadata["chunk_size"],
            "chunk_overlap": metadata["chunk_overlap"],
            "token_count": metadata["token_count"],
            "path": metadata["path"],
            "doc_hash": doc_hash
        }
    except Exception:
        return None

def save_persistent_index(
    pdf_path: str,
    full_text: str,
    chunks: list[str],
    index: faiss.Index,
    token_count: int,
    chunk_size: int = 500,
    chunk_overlap: int = 100
) -> str:
    """
    Saves FAISS index binary and metadata to disk persistent cache.
    """
    _ensure_cache_dirs()
    doc_hash = get_doc_hash(pdf_path, chunk_size, chunk_overlap)
    abs_path = os.path.abspath(pdf_path)
    
    # Save FAISS index binary
    index_file = os.path.join(INDEXES_DIR, f"{doc_hash}.index")
    faiss.write_index(index, index_file)
    
    # Save metadata entry
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        all_metadata = json.load(f)
        
    all_metadata[doc_hash] = {
        "full_text": full_text,
        "chunks": chunks,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "token_count": token_count,
        "path": abs_path,
        "doc_hash": doc_hash
    }
    
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, indent=2)
        
    return doc_hash
