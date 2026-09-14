import io
import threading
import numpy as np
import faiss
from core.ingestion.parser import extract_text_from_pdf
from core.ingestion.chunker import chunk_text
from core.vectorstore.embeddings import get_embedding_model

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
