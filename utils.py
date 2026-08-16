
import re
import tiktoken
import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# Global cache for models (works in both Streamlit and non-Streamlit contexts)
_embedding_model_cache = None
_encoder_cache = None

def _is_streamlit_context():
    """Check if we're running inside Streamlit."""
    try:
        import streamlit as st
        # Try to access session_state, which only exists in Streamlit context
        _ = st.session_state
        return True
    except (ImportError, AttributeError, RuntimeError):
        return False

def _streamlit_cache(func):
    """Decorator that applies Streamlit caching only if in Streamlit context."""
    if _is_streamlit_context():
        import streamlit as st
        return st.cache_resource(show_spinner=f"Loading {func.__name__}...")(func)
    return func

def get_embedding_model():
    """Load embedding model with caching that works in both Streamlit and non-Streamlit contexts."""
    global _embedding_model_cache
    
    if _embedding_model_cache is not None:
        return _embedding_model_cache
    
    try:
        import torch
        import os
        # Suppress Streamlit's file watcher from introspecting transformers internals
        # which causes floods of harmless torchvision ModuleNotFoundError log noise
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        torch.set_num_threads(max(1, torch.get_num_threads()))

        # all-mpnet-base-v2 peaks at ~4.3GB during encode on Cloud Run CPU
        # (PyTorch inference working memory + model weights + embeddings buffer)
        # which exceeds the 4Gi limit. all-MiniLM-L6-v2 stays well under 2GB
        # with comparable retrieval quality for this use case.
        _embedding_model_cache = SentenceTransformer('all-MiniLM-L6-v2')
        return _embedding_model_cache
    except Exception as e:
        return None

def get_encoder():
    """Load tokenizer with caching that works in both Streamlit and non-Streamlit contexts."""
    global _encoder_cache
    
    if _encoder_cache is not None:
        return _encoder_cache
    
    try:
        _encoder_cache = tiktoken.get_encoding("cl100k_base")
        return _encoder_cache
    except Exception:
        return None

def extract_text_from_pdf(pdf_file, progress_callback=None) -> str:
    """Extracts all text from a given uploaded PDF file."""
    reader = PdfReader(pdf_file)
    text = ""
    total_pages = len(reader.pages)
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
        if progress_callback:
            progress_callback(i + 1, total_pages)
    return text

def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """
    Splits text into chunks using LangChain's RecursiveCharacterTextSplitter.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    # Approximate words to characters (avg 5 chars per word)
    char_chunk_size = chunk_size * 5
    char_chunk_overlap = chunk_overlap * 5
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=char_chunk_size,
        chunk_overlap=char_chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    
    chunks = text_splitter.split_text(text)
    return chunks

def count_tokens(text: str) -> int:
    """Counts tokens in a string using tiktoken."""
    enc = get_encoder()
    if enc is None:
        # Fallback approximation: 1 token ~= 4 characters
        return len(text) // 4
    return len(enc.encode(text))


def build_faiss_index(chunks: list[str], api_key: str, show_progress: bool = True):
    """
    Embeds the chunks using the local SentenceTransformer model and builds a FAISS index.
    Returns the index and the embeddings.

    show_progress=True  — renders a Streamlit progress bar (Streamlit runtime required).
    show_progress=False — silent mode, safe to call outside Streamlit (e.g. MCP server).
    """
    import numpy as np
    import faiss

    embedding_model = get_embedding_model()
    if embedding_model is None:
        error_msg = "Local embedding model failed to load. Please install sentence-transformers."
        if show_progress:
            try:
                import streamlit as st
                st.error(error_msg)
                st.stop()
            except:
                raise RuntimeError(error_msg)
        else:
            raise RuntimeError(error_msg)

    progress_bar = None
    if show_progress:
        try:
            import streamlit as st
            progress_bar = st.progress(0, text="Embedding chunks locally (this may take a moment)...")
        except:
            pass  # Streamlit not available, continue without progress bar

    # SentenceTransformer encodes a list of strings into a numpy array
    embeddings = embedding_model.encode(chunks, show_progress_bar=False)

    if progress_bar:
        progress_bar.progress(1.0, text="Embedding complete!")
        progress_bar.empty()

    embeddings = np.array(embeddings, dtype=np.float32)
    dimension = embeddings.shape[1]

    # Create L2 distance index
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    return index, embeddings

def search_chunks(query: str, index, chunks: list[str], api_key: str, top_k: int = 3) -> list[str]:
    """
    Embeds the query locally, searches the FAISS index, and returns the top_k chunks.
    Uses query expansion to improve retrieval for complex/broad queries.
    Applies keyword-boosted re-ranking so chunks containing terms from the query
    rank higher, catching specific factual answers that vector similarity alone misses.
    """
    import numpy as np

    embedding_model = get_embedding_model()
    if embedding_model is None:
        return []

    # --- Query Expansion ---
    # Generates multiple sub-queries so that paraphrased or conditional phrasing
    # (e.g. "when source file is open") still maps onto the correct chunks.
    sub_queries = _expand_query(query)
    all_queries = [query] + sub_queries

    seen_indices = set()
    candidate_chunks = []  # list of (distance, idx, chunk_text)

    for q in all_queries:
        query_vector = embedding_model.encode([q])
        query_vector = np.array(query_vector, dtype=np.float32)

        # Fetch a generous pool — 5× top_k — to leave room for re-ranking
        fetch_k = min(top_k * 5, len(chunks))
        distances, indices = index.search(query_vector, fetch_k)

        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(chunks) and idx not in seen_indices:
                seen_indices.add(idx)
                candidate_chunks.append((dist, idx, chunks[idx]))

    # --- Keyword-Boosted Re-ranking ---
    # Vector similarity captures semantic closeness but can miss specific
    # operational details buried in a chunk (e.g. "protected exclusion mode").
    # We subtract a bonus from the L2 distance for each query keyword that
    # appears in the chunk, so these chunks float to the top.
    query_keywords = _extract_keywords(query)
    KEYWORD_BONUS = 0.08  # distance reduction per matched keyword

    def adjusted_distance(dist, chunk_text):
        chunk_lower = chunk_text.lower()
        matched = sum(1 for kw in query_keywords if kw in chunk_lower)
        return dist - (matched * KEYWORD_BONUS)

    candidate_chunks.sort(key=lambda x: adjusted_distance(x[0], x[2]))

    # Apply a relaxed similarity threshold — generous enough to keep relevant
    # conditional/factual chunks that score slightly worse on pure vector distance.
    SIMILARITY_THRESHOLD = 2.0
    filtered = [chunk for dist, idx, chunk in candidate_chunks if dist <= SIMILARITY_THRESHOLD]

    # If threshold still filters everything out, fall back to raw top_k
    if not filtered:
        filtered = [chunk for _, _, chunk in candidate_chunks[:top_k]]

    return filtered[:top_k]


def _extract_keywords(query: str) -> list[str]:
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
        # common instruction verbs that add no retrieval signal
        "summarize", "summarise", "explain", "describe", "list", "give",
        "tell", "provide", "find", "show", "get", "extract", "identify",
    }
    words = re.findall(r"[a-z0-9]+", query.lower())
    return [w for w in words if w not in stop_words and len(w) > 2]


def _expand_query(query: str) -> list[str]:
    """
    Generates sub-queries from the original query to improve retrieval recall.

    Strategy:
    1. Strip leading instruction verbs to expose the core topic.
    2. Preserve conditional/contextual clauses (e.g. "when X", "if X is open")
       as standalone sub-queries — these often map directly onto factual chunks.
    3. Add a keyword-only fallback sub-query for broad queries.

    e.g. "fup copy command when source file is open" →
         ["fup copy source file open",
          "when source file is open",
          "source file open",
          "fup copy"]
    """
    query_lower = query.lower().strip()

    # Strip common instructional prefixes to get the core topic
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

    # 1. Core topic without instruction prefix
    if core_topic and core_topic != query_lower and len(core_topic) > 3:
        sub_queries.append(core_topic)

    # 2. Extract conditional/contextual clauses — "when X", "if X", "while X"
    #    These are the high-value sub-queries for "how does X behave when Y" questions.
    conditional_pattern = re.compile(
        r'\b(when|if|while|during|after|before|unless|until)\b(.{3,60})',
        re.IGNORECASE
    )
    for match in conditional_pattern.finditer(query_lower):
        clause = match.group(0).strip()
        if clause not in sub_queries:
            sub_queries.append(clause)
        # Also add just the noun phrase after the conditional keyword
        noun_phrase = match.group(2).strip()
        if noun_phrase and noun_phrase not in sub_queries:
            sub_queries.append(noun_phrase)

    # 3. Keyword-only fallback (first 3 significant words)
    keywords = _extract_keywords(query)
    if keywords:
        keyword_query = " ".join(keywords[:3])
        if keyword_query not in sub_queries and keyword_query != core_topic:
            sub_queries.append(keyword_query)

    return sub_queries

def generate_gemini_response(api_key: str, context: str, query: str) -> str:
    """
    Sends the context and query to Gemini using the REST API to bypass module issues.
    """
    import requests
    
    if not api_key:
        return "Error: Please provide a Gemini API key."
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
You are an expert assistant helping users understand a document.
Answer the user's query using the provided context excerpts from the document.
The context is a set of the most relevant sections retrieved from the full document.

Guidelines:
- Base your answer primarily on the provided context.
- If the context contains partial information, use it to give the best possible answer.
- If the context is insufficient to fully answer, provide what you can and clearly note what is missing.
- Do NOT refuse to answer if the context contains any relevant information at all.
- Keep your answer concise and focused on the query.

Context (retrieved document sections):
{context}

Query:
{query}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    import time
    max_retries = 4
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            data = response.json()
            
            # Extract text from response
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                return "Error parsing response from Gemini API: " + str(data)
                
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                return f"Error communicating with Gemini API after {max_retries} attempts: {str(e)}"

def generate_gemini_vertex(context: str, query: str) -> str:
    """
    Sends the context and query to Gemini using the google-genai SDK for Vertex AI.
    Used when running in Cloud Run with Workload Identity.
    """
    try:
        from google import genai
    except ImportError:
        return "Error: google-genai library is not installed."
        
    prompt = f"""
You are an expert assistant helping users understand a document.
Answer the user's query using the provided context excerpts from the document.
The context is a set of the most relevant sections retrieved from the full document.

Guidelines:
- Base your answer primarily on the provided context.
- If the context contains partial information, use it to give the best possible answer.
- If the context is insufficient to fully answer, provide what you can and clearly note what is missing.
- Do NOT refuse to answer if the context contains any relevant information at all.
- Keep your answer concise and focused on the query.

Context (retrieved document sections):
{context}

Query:
{query}
"""
    try:
        client = genai.Client(vertexai=True, project="singla", location="europe-west3")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text if response.text is not None else "No response generated from Vertex AI"
    except Exception as e:
        return f"Error communicating with Vertex AI: {str(e)}"

import threading

class DocumentProcessorThread(threading.Thread):
    def __init__(self, uploaded_file_bytes, chunk_size, chunk_overlap, api_key):
        super().__init__()
        self.uploaded_file_bytes = uploaded_file_bytes
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.api_key = api_key
        
        self.result_index = None
        self.result_embeddings = None
        self.result_chunks = None
        self.result_full_text = None
        self.error = None
        self.is_done = False
        self.progress_msg = "Initializing..."
        self.progress_pct = 0.0

    def run(self):
        try:
            import io
            import numpy as np
            import faiss
            
            self.progress_msg = "Extracting text from PDF..."
            self.progress_pct = 0.05
            
            pdf_io = io.BytesIO(self.uploaded_file_bytes)
            
            def pdf_callback(current, total):
                self.progress_msg = f"Extracting text from PDF (Page {current}/{total})..."
                self.progress_pct = 0.05 + (0.20 * current / max(1, total))
                
            full_text = extract_text_from_pdf(pdf_io, progress_callback=pdf_callback)
            if not full_text.strip():
                self.error = "Could not extract text from the PDF."
                return
                
            self.progress_msg = "Splitting text into chunks..."
            self.progress_pct = 0.25
            chunks = chunk_text(full_text, chunk_size=int(self.chunk_size), chunk_overlap=int(self.chunk_overlap))
            
            self.progress_msg = "Loading embedding model..."
            self.progress_pct = 0.30
            embedding_model = get_embedding_model()
            if embedding_model is None:
                self.error = "Local embedding model failed to load."
                return
                
            total_chunks = len(chunks)
            self.progress_msg = f"Embedding {total_chunks} chunks..."
            self.progress_pct = 0.40

            # Encode all chunks in one call — SentenceTransformer handles
            # internal batching more efficiently than a manual Python loop.
            # batch_size=128 keeps memory reasonable while maximising CPU throughput.
            all_embeddings = embedding_model.encode(
                chunks,
                batch_size=128,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=False
            )

            self.progress_pct = 0.95
                
            self.progress_msg = "Building vector index..."
            self.progress_pct = 0.98
            
            embeddings_np = np.array(all_embeddings, dtype=np.float32)
            dimension = embeddings_np.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings_np)
            
            self.progress_msg = "Complete!"
            self.progress_pct = 1.0
            
            self.result_full_text = full_text
            self.result_chunks = chunks
            self.result_index = index
            self.result_embeddings = embeddings_np
        except Exception as e:
            self.error = str(e)
        finally:
            self.is_done = True

