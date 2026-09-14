"""
Unit test for Persistent Vector Store Cache.
"""

import os
import sys
import time
sys.path.insert(0, '.')

from core.vectorstore.persistent_store import load_persistent_index, save_persistent_index, get_doc_hash
from core.vectorstore.faiss_store import build_faiss_index
import mcp_server

def test_persistence():
    pdf_path = os.path.abspath("resources/vanguards_principles_for_investing_success.pdf")
    assert os.path.exists(pdf_path), "Sample PDF missing"

    print("1. Testing first-time indexing (cold cache)...")
    t0 = time.time()
    entry1 = mcp_server._ensure_indexed(pdf_path)
    dur1 = time.time() - t0
    print(f"   Cold Index Time: {dur1:.2f}s, Chunks: {len(entry1['chunks'])}, Tokens: {entry1['token_count']}")

    print("\n2. Testing persistent index load (warm disk cache)...")
    # Clear in-memory cache to simulate brand new process session
    mcp_server._cache.clear()
    
    t0 = time.time()
    entry2 = mcp_server._ensure_indexed(pdf_path)
    dur2 = time.time() - t0
    print(f"   Warm Disk Index Load Time: {dur2:.4f}s")
    
    assert entry1["token_count"] == entry2["token_count"]
    assert len(entry1["chunks"]) == len(entry2["chunks"])
    assert dur2 < 0.1, f"Disk index load took too long: {dur2:.4f}s"

    print("\n✅ Persistent disk index unit test passed!")

if __name__ == "__main__":
    test_persistence()
