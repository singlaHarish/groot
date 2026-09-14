import numpy as np
import faiss
from core.vectorstore.embeddings import get_embedding_model

def build_faiss_index(chunks: list[str], api_key: str = None, show_progress: bool = True):
    """
    Embeds the chunks using the local SentenceTransformer model and builds a FAISS index.
    Returns the index and the embeddings.
    """
    embedding_model = get_embedding_model()
    if embedding_model is None:
        error_msg = "Local embedding model failed to load. Please install sentence-transformers."
        if show_progress:
            try:
                import streamlit as st
                st.error(error_msg)
                st.stop()
            except Exception:
                raise RuntimeError(error_msg)
        else:
            raise RuntimeError(error_msg)

    progress_bar = None
    if show_progress:
        try:
            import streamlit as st
            progress_bar = st.progress(0, text="Embedding chunks locally (this may take a moment)...")
        except Exception:
            pass

    embeddings = embedding_model.encode(chunks, show_progress_bar=False)

    if progress_bar:
        progress_bar.progress(1.0, text="Embedding complete!")
        progress_bar.empty()

    embeddings = np.array(embeddings, dtype=np.float32)
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    return index, embeddings
