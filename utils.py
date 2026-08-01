
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
        return SentenceTransformer('all-MiniLM-L6-v2')
    except Exception:
        return None

@st.cache_resource(show_spinner="Loading tokenizer...")
def get_encoder():
    try:
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return None

def extract_text_from_pdf(pdf_file) -> str:
    """Extracts all text from a given uploaded PDF file."""
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """
    Splits text into chunks by roughly the specified number of words/tokens.
    For simplicity, we do a basic character/word split.
    """
    # Simple split by paragraphs and sentences
    words = text.split()
    chunks = []
    
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - chunk_overlap
        
        # Prevent infinite loop if overlap >= size
        if chunk_size - chunk_overlap <= 0:
            break
            
    return chunks

def count_tokens(text: str) -> int:
    """Counts tokens in a string using tiktoken."""
    enc = get_encoder()
    if enc is None:
        # Fallback approximation: 1 token ~= 4 characters
        return len(text) // 4
    return len(enc.encode(text))


def build_faiss_index(chunks: list[str], api_key: str):
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
        
    progress_bar = st.progress(0, text="Embedding chunks locally (this may take a moment)...")
    
    # SentenceTransformer encodes a list of strings into a numpy array
    embeddings = embedding_model.encode(chunks, show_progress_bar=False)
    
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
    """
    import numpy as np
    
    embedding_model = get_embedding_model()
    if embedding_model is None:
        return []
        
    query_vector = embedding_model.encode([query])
    query_vector = np.array(query_vector, dtype=np.float32)
    
    # search returns distances and indices
    distances, indices = index.search(query_vector, top_k)
    
    results = []
    for idx in indices[0]:
        if idx != -1 and idx < len(chunks):
            results.append(chunks[idx])
            
    return results

def generate_gemini_response(api_key: str, context: str, query: str) -> str:
    """
    Sends the context and query to Gemini using the REST API to bypass module issues.
    """
    import requests
    
    if not api_key:
        return "Error: Please provide a Gemini API key."
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
You are an expert assistant. Please answer the user's query based ONLY on the provided context. 
If the context does not contain the answer, say "I cannot answer this based on the provided document."

Context:
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
You are an expert assistant. Please answer the user's query based ONLY on the provided context. 
If the context does not contain the answer, say "I cannot answer this based on the provided document."

Context:
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
