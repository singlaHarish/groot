
import re
import tiktoken
import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import streamlit as st

@st.cache_resource(show_spinner="Loading embedding model...")
def get_embedding_model():
    try:
        # all-mpnet-base-v2 is significantly better at semantic similarity
        # than all-MiniLM-L6-v2 for complex/multi-topic queries
        return SentenceTransformer('all-mpnet-base-v2')
    except Exception:
        try:
            # Fallback to MiniLM if mpnet unavailable
            return SentenceTransformer('all-MiniLM-L6-v2')
        except Exception:
            return None

@st.cache_resource(show_spinner="Loading tokenizer...")
def get_encoder():
    try:
        return tiktoken.get_encoding("cl100k_base")
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
    """
    import numpy as np
    import faiss
    import streamlit as st
    
    embedding_model = get_embedding_model()
    if embedding_model is None:
        st.error("Local embedding model failed to load. Please install sentence-transformers.")
        st.stop()
        
    if show_progress:
        progress_bar = st.progress(0, text="Embedding chunks locally (this may take a moment)...")
    
    # SentenceTransformer encodes a list of strings into a numpy array
    embeddings = embedding_model.encode(chunks, show_progress_bar=False)
    
    if show_progress:
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
    Filters out chunks with low similarity (distance too high) to avoid irrelevant context.
    """
    import numpy as np
    
    embedding_model = get_embedding_model()
    if embedding_model is None:
        return []

    # --- Query Expansion ---
    # For broad/complex queries, we generate sub-queries and merge their results.
    # This significantly improves recall for multi-aspect queries like
    # "summarize risk factors" or "what are the key recommendations".
    sub_queries = _expand_query(query)
    all_queries = [query] + sub_queries

    seen_indices = set()
    candidate_chunks = []  # list of (distance, chunk_text)

    for q in all_queries:
        query_vector = embedding_model.encode([q])
        query_vector = np.array(query_vector, dtype=np.float32)

        # Retrieve more candidates than top_k, then re-rank
        fetch_k = min(top_k * 3, len(chunks))
        distances, indices = index.search(query_vector, fetch_k)

        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(chunks) and idx not in seen_indices:
                seen_indices.add(idx)
                candidate_chunks.append((dist, chunks[idx]))

    # Sort by distance (lower = more similar in L2) and take top_k
    candidate_chunks.sort(key=lambda x: x[0])

    # Apply similarity threshold — discard chunks that are too dissimilar.
    # L2 distance threshold of 1.5 works well for all-mpnet-base-v2 (384-dim).
    # For all-MiniLM-L6-v2 (384-dim), same threshold applies.
    SIMILARITY_THRESHOLD = 1.5
    filtered = [chunk for dist, chunk in candidate_chunks if dist <= SIMILARITY_THRESHOLD]

    # If threshold filters everything out (very broad query), fall back to raw top_k
    if not filtered:
        filtered = [chunk for _, chunk in candidate_chunks[:top_k]]

    return filtered[:top_k]


def _expand_query(query: str) -> list[str]:
    """
    Generates sub-queries from the original query to improve retrieval recall.
    Handles broad/instructional queries that don't map well to factual chunk text.
    
    e.g. "Summarize the main risk factors" →
         ["risk factors", "risks", "main risks in the document"]
    """
    query_lower = query.lower().strip()

    # Strip common instructional prefixes to get the core topic
    instruction_prefixes = [
        "summarize", "summarise", "explain", "describe", "list",
        "what are", "what is", "tell me about", "give me", "provide",
        "extract", "find", "identify", "outline"
    ]

    core_topic = query_lower
    for prefix in instruction_prefixes:
        if core_topic.startswith(prefix):
            core_topic = core_topic[len(prefix):].strip().lstrip("the ").strip()
            break

    sub_queries = []

    # Add the core topic as a sub-query if it differs from the original
    if core_topic and core_topic != query_lower and len(core_topic) > 3:
        sub_queries.append(core_topic)

    # Add a noun-phrase variant
    if len(core_topic.split()) > 1:
        sub_queries.append(core_topic.split()[0])  # First keyword alone

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
        return response.text
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
            batch_size = 32
            all_embeddings = []
            
            for i in range(0, total_chunks, batch_size):
                self.progress_msg = f"Embedding chunks: {i}/{total_chunks}..."
                self.progress_pct = 0.30 + (0.65 * min(i, total_chunks) / max(1, total_chunks))
                batch = chunks[i:i+batch_size]
                emb = embedding_model.encode(batch, show_progress_bar=False)
                all_embeddings.extend(emb)
                
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

