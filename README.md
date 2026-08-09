# 🌿 Groot - AI Document Context Optimizer

A cutting-edge, interactive Streamlit application that optimizes document retrieval and reduces AI language model costs through intelligent vector-based context chunking and retrieval.

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Installation](#installation)
- [Running Locally](#running-locally)
- [Project Structure](#project-structure)
- [Usage Guide](#usage-guide)
- [Technology Stack](#technology-stack)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Environment Impact](#environment-impact)

---

## 🎯 Overview

**Groot** is an enterprise-grade document optimization platform designed to reduce AI language model costs while maintaining response quality. It leverages FAISS vector search and semantic embeddings to intelligently extract only the most relevant document context needed to answer user queries.

### The Problem It Solves

When processing large documents (PDFs, reports, etc.) with AI models, organizations typically pass the entire document as context, leading to:
- **High token consumption** and inflated API costs
- **Slower inference times** due to context bloat
- **Wasted computational resources** processing irrelevant information

### The Solution

Groot uses semantic vector search with multi-stage retrieval to:
1. Extract and chunk documents intelligently using LangChain's `RecursiveCharacterTextSplitter`
2. Build a FAISS vector index for sub-millisecond retrieval
3. Expand queries into multiple sub-queries (including conditional clause extraction) to improve recall
4. Re-rank candidates using keyword-boosted scoring to surface specific factual chunks
5. Retrieve only the top-K most relevant chunks matching your query
6. Reduce context size by up to 96% while maintaining response quality
7. Compare costs and responses side-by-side

---

## ✨ Key Features

### 1. **Interactive Document Upload & Processing**
- Upload PDF documents directly through the web interface
- Automatic text extraction using pypdf
- Background thread processing with real-time progress feedback
- Configurable chunk sizing and overlap

### 2. **Multi-Stage Vector Retrieval Pipeline**
- **Query Expansion:** Each query is decomposed into multiple sub-queries:
  - Instruction prefix stripping (removes "summarize", "explain", etc.)
  - Conditional clause extraction — "when X", "if X", "while X" phrases become dedicated sub-queries, directly targeting factual/operational chunks
  - Keyword-only fallback for broad queries
- **FAISS Vector Search:** Each sub-query searches a 5× top_k candidate pool independently; results are deduplicated and merged
- **Keyword-Boosted Re-ranking:** Candidates are re-scored by subtracting a distance bonus for each query keyword present in the chunk — catches specific details that pure vector similarity misses
- **Relaxed Similarity Threshold:** L2 distance threshold of 2.0 keeps borderline-relevant chunks in the candidate pool before re-ranking

### 3. **Token & Cost Analysis**
- Real-time token counting using tiktoken (cl100k_base encoding)
- Cost calculations based on your API pricing
- Side-by-side comparison of unoptimized vs optimized context
- Savings metrics (percentage & dollar amount)

### 4. **Dual LLM Response Comparison**
- Generate responses using full unoptimized context
- Generate responses using Groot-optimized context
- Visual comparison to verify quality parity
- Side-by-side layout for easy analysis

### 5. **Multi-Backend Support**
- **API Key (Local):** Google Gemini REST API with exponential-backoff retry (4 attempts)
- **Vertex AI (Cloud Run):** `gemini-2.5-flash` via `google-genai` SDK with Workload Identity — no API key required in production

### 6. **Beautiful Dark Theme UI**
- Modern organic wood & forest color scheme
- Responsive design (desktop and mobile with hamburger drawer)
- Glassmorphism cards with gradient accents
- Smooth animations and intuitive navigation

### 7. **Settings & Configuration**
- Adjustable chunk size and overlap
- Top-K retrieval parameter tuning (slider, 1–20)
- Model backend selection and API key management
- Cost-per-million-tokens configuration

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GROOT FRONTEND                       │
│              (Streamlit Web Application)                │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
    ┌───▼───┐   ┌──▼───┐    ┌──▼────┐
    │ PDF   │   │Query │    │Config │
    │Upload │   │Input │    │Panel  │
    └───┬───┘   └──┬───┘    └───┬───┘
        │          │            │
        └──────────┼────────────┘
                   │
        ┌──────────▼──────────┐
        │   TEXT EXTRACTION   │
        │    (pypdf lib)      │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────────────────┐
        │  TEXT CHUNKING                  │
        │  LangChain RecursiveCharacter   │
        │  TextSplitter                   │
        │  (configurable word size &      │
        │   overlap → converted to chars) │
        └──────────┬─────────────────────┘
                   │
        ┌──────────▼──────────────────────┐
        │  VECTOR EMBEDDING & INDEXING    │
        │  all-MiniLM-L6-v2 (384-dim)     │
        │  batch_size=128, FAISS L2 index │
        │  (background thread, non-       │
        │   blocking UI)                  │
        └──────────┬─────────────────────┘
                   │
        ┌──────────▼──────────────────────┐
        │   MULTI-STAGE RETRIEVAL         │
        │                                 │
        │  1. Query Expansion             │
        │     • Strip instruction prefix  │
        │     • Extract conditional       │
        │       clauses (when/if/while)   │
        │     • Keyword fallback          │
        │                                 │
        │  2. FAISS Search                │
        │     • 5× top_k candidate pool   │
        │     • Per sub-query, deduplicated│
        │                                 │
        │  3. Keyword-Boosted Re-ranking  │
        │     • -0.08 L2 dist per keyword │
        │       match in chunk            │
        │                                 │
        │  4. Similarity Threshold        │
        │     • L2 ≤ 2.0 (falls back to   │
        │       raw top_k if all filtered) │
        └──────────┬─────────────────────┘
                   │
        ┌──────────▼──────────────────────┐
        │   LLM RESPONSE GENERATION       │
        │                                 │
        │  • API Key mode:                │
        │    Gemini REST + retry (4×)     │
        │  • Vertex AI mode:              │
        │    gemini-2.5-flash via         │
        │    google-genai SDK             │
        └──────────┬─────────────────────┘
                   │
        ┌──────────▼──────────────────────┐
        │   METRICS & COMPARISON DISPLAY  │
        │   (Cost, tokens, responses)     │
        └──────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- pip package manager
- Google Gemini API key (or Vertex AI credentials for Cloud Run)
- Git (optional)

### Installation

1. **Clone or Download the Repository**
```bash
git clone <repository-url>
cd groot
```

2. **Create Virtual Environment**
```bash
python -m venv .venv
```

3. **Activate Virtual Environment**

   **Windows:**
   ```bash
   .venv\Scripts\activate
   ```
   
   **macOS/Linux:**
   ```bash
   source .venv/bin/activate
   ```

4. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### Running Locally

**Start the Streamlit App:**
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`

---

## 📁 Project Structure

```
groot/
├── app.py                          # Main Streamlit application & page router
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker containerization
├── README.md                       # This file
├── utils.py                        # Core retrieval pipeline
│                                   #  ├─ extract_text_from_pdf
│                                   #  ├─ chunk_text (LangChain splitter)
│                                   #  ├─ build_faiss_index
│                                   #  ├─ search_chunks (multi-stage retrieval)
│                                   #  ├─ _expand_query (conditional clause extraction)
│                                   #  ├─ _extract_keywords (stop-word filtered)
│                                   #  ├─ generate_gemini_response (REST + retry)
│                                   #  ├─ generate_gemini_vertex (Vertex AI SDK)
│                                   #  └─ DocumentProcessorThread (background worker)
│
├── components/                     # Reusable UI components
│   ├── header.py                   # Navigation header with logo
│   └── settings.py                 # Settings modal and config state
│
├── sections/                       # Landing page sections
│   ├── hero.py                     # Hero section intro
│   ├── technology.py               # Technology stack overview
│   ├── cost_savings.py             # Cost analysis showcase
│   ├── connectors.py               # Enterprise integrations
│   ├── environment.py              # Environmental impact
│   ├── integration.py              # Integration pipelines
│   ├── footer_cta.py               # Call-to-action footer
│   └── optimizer.py                # Main optimizer tool (page 2)
│
├── image/                          # Static assets
│   └── groot-logo.png              # Brand logo
│
├── resources/                      # Sample documents for testing
│   ├── Indian Paneer recipies.pdf
│   └── vanguards_principles_for_investing_success.pdf
│
└── .github/
    └── workflows/
        ├── deploy.yml              # CI/CD deploy pipeline
        └── uninstall.yml           # CI/CD teardown pipeline
```

---

## 💻 Usage Guide

### Step 1: Upload a Document
- Click **"Upload Document (PDF)"** in the optimizer page
- Select a PDF file from your computer
- Processing runs in a background thread — a progress bar tracks extraction → chunking → embedding → indexing

### Step 2: Enter Your Query
- Type your search query or prompt in the **"Enter Search Query / Prompt"** field
- Examples:
  - "Summarize the main risk factors"
  - "What are the key financial metrics?"
  - "fup copy command when source file is open"

### Step 3: Click "Optimize and Compare"
- The retrieval pipeline will:
  - Expand your query into multiple sub-queries (including conditional clauses)
  - Search FAISS with a 5× candidate pool per sub-query
  - Re-rank candidates using keyword-boosted scoring
  - Apply a similarity threshold and return the top-K chunks
  - Generate responses using both full and optimized contexts
  - Display token counts, costs, and savings

### Step 4: Review Results
- **Section 2:** View token reduction and cost savings metrics
- **Section 3:** Compare side-by-side LLM responses from both approaches

### Step 5: Adjust Settings (Optional)
- Click **"⚙️ Settings"** to fine-tune:
  - **Backend:** API Key (Local) or Vertex AI (Cloud Run)
  - **API Key:** Your Google Gemini API key
  - **Chunk Size:** Words per chunk (default: 500)
  - **Chunk Overlap:** Overlap between chunks in words (default: 100)
  - **Top-K:** Chunks to retrieve (default: 8, range 1–20)
  - **Cost/1M tokens:** Adjust to match your API pricing

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit | Web UI framework |
| **Text Splitting** | LangChain `RecursiveCharacterTextSplitter` | Semantic-aware chunking |
| **Embeddings** | `all-MiniLM-L6-v2` (Sentence-Transformers) | 384-dim local embeddings, <2GB RAM |
| **Vector DB** | FAISS `IndexFlatL2` | Fast L2 similarity search |
| **Retrieval** | Multi-query expansion + keyword re-ranking | High-recall factual retrieval |
| **LLM (local)** | Google Gemini REST API | Response generation with retry |
| **LLM (cloud)** | `gemini-2.5-flash` via Vertex AI SDK | Cloud Run production backend |
| **PDF Processing** | pypdf | PDF text extraction |
| **Tokenization** | tiktoken `cl100k_base` | Token counting |
| **Numerics** | NumPy | Embeddings & distance math |
| **Concurrency** | `threading.Thread` | Non-blocking document processing |

### Key Dependencies

```
streamlit               # Web framework
pypdf                   # PDF text extraction
tiktoken                # Token counting
sentence-transformers   # all-MiniLM-L6-v2 embeddings
faiss-cpu               # Vector search index
langchain-text-splitters # RecursiveCharacterTextSplitter
google-generativeai     # Gemini API (local mode)
google-genai            # Vertex AI SDK (cloud mode)
numpy                   # Numerical computing
```

---

## ⚙️ Configuration

### Settings Panel (Runtime)

Access via the **⚙️ Settings** button in the app. All settings are stored in `st.session_state`:

```python
{
    "backend": "Vertex AI (Cloud Run)",  # or "API Key (Local)"
    "api_key": "VERTEX_AI_MODE",         # or your Gemini API key
    "cost_per_1m": 3.50,                 # Cost per 1M input tokens ($)
    "chunk_size": 500,                   # Words per chunk
    "chunk_overlap": 100,                # Overlap between chunks (words)
    "top_k": 8                           # Chunks to retrieve
}
```

### Tuning Parameters

| Parameter | Default | Guidance |
|-----------|---------|----------|
| **Chunk Size** | 500 words | Larger chunks preserve more context but reduce precision. 300–700 works well for most docs. |
| **Chunk Overlap** | 100 words | Prevents facts from being split across chunk boundaries. 50–150 recommended. |
| **Top-K** | 8 | More chunks = better recall but higher token count. 5–12 is the useful range. |
| **Cost/1M** | $3.50 | Set to your actual API tier pricing for accurate savings display. |

### Retrieval Pipeline Constants (in `utils.py`)

| Constant | Value | Purpose |
|----------|-------|---------|
| `KEYWORD_BONUS` | 0.08 | L2 distance reduction per matched keyword during re-ranking |
| `SIMILARITY_THRESHOLD` | 2.0 | Maximum L2 distance to include a chunk (falls back to raw top_k if all filtered) |
| Candidate pool | 5× top_k | FAISS fetch size per sub-query before re-ranking |
| Embedding model | `all-MiniLM-L6-v2` | Chosen for <2GB memory footprint on Cloud Run CPU instances |

---

## 🐳 Deployment

### Docker

```bash
# Build image
docker build -t groot:latest .

# Run container
docker run -p 8080:8080 groot:latest
```

Access at: `http://localhost:8080`

For local API key mode:
```bash
docker run -p 8080:8080 -e GOOGLE_API_KEY=your_key_here groot:latest
```

### Cloud Run (Vertex AI mode)

The app auto-detects Vertex AI when `backend` is set to `"Vertex AI (Cloud Run)"`. It uses Workload Identity — no API key required. The Vertex client is initialized as:

```python
client = genai.Client(vertexai=True, project="singla", location="europe-west3")
```

### CI/CD Pipelines

| Workflow | File | Purpose |
|----------|------|---------|
| Deploy | `.github/workflows/deploy.yml` | Build and deploy to Cloud Run |
| Uninstall | `.github/workflows/uninstall.yml` | Tear down Cloud Run service |

---

## 🌱 Environment Impact

Groot reduces environmental impact through token reduction:

1. **Reduced Computation:** Fewer tokens processed = fewer GPU/CPU cycles at the data center
2. **Lower Energy Usage:** Smaller context → faster inference → less power per query
3. **Proportional Carbon Savings:** Token reduction translates directly to proportional energy savings

**Real Example (from testing):**
- 135,000 token document → 5,000 token optimized context
- **96% token reduction** on a single query
- At scale (1M queries/day), this represents substantial CO₂ and cost savings

---

## 📊 Performance

### Typical Results

| Metric | Unoptimized | Optimized | Improvement |
|--------|-------------|-----------|-------------|
| **Tokens/Query** | 135,000 | 5,000 | ~96% ↓ |
| **Cost/Query** | $0.473 | $0.018 | ~96% ↓ |
| **Vector Search** | — | <1ms | Sub-millisecond |
| **Response Quality** | Baseline | Maintained | ✓ |

### Scalability

- **Small Documents** (< 50 pages): near-instant processing
- **Medium Documents** (50–500 pages): < 5 seconds
- **Large Documents** (500+ pages): < 30 seconds
- **Vector Search:** Sub-millisecond regardless of document size

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- [ ] Support for additional document formats (DOCX, TXT, HTML)
- [ ] Multi-document search across collections
- [ ] Re-ranker model (cross-encoder) for higher precision
- [ ] Advanced analytics dashboard
- [ ] API endpoint for programmatic access
- [ ] Caching layer for frequently searched documents

---

## 🆘 Support & Troubleshooting

**"API Key not found"**
→ Click ⚙️ Settings and enter your Google Gemini API key. Get one at https://makersuite.google.com/app/apikey

**"Could not extract text from PDF"**
→ Ensure the PDF is text-based (not a scanned image). Use an OCR tool to convert scanned PDFs first.

**"FAISS installation error"**
→ `pip install faiss-cpu` works on all platforms including Apple Silicon.

**Optimized response is missing specific details**
→ Increase Top-K in Settings (try 10–15). The retrieval pipeline uses multi-query expansion and keyword re-ranking to surface specific factual chunks, but very narrow facts may require more candidates.

---

## 🗺️ Roadmap

**Q3 2026:**
- [ ] Multi-file batch processing
- [ ] Real-time cost tracking dashboard
- [ ] Cross-encoder re-ranker for higher precision
- [ ] REST API endpoints

**Q4 2026:**
- [ ] Advanced analytics and insights
- [ ] Document collection management
- [ ] Team collaboration features
- [ ] Enterprise SSO integration

---

## 🙏 Acknowledgments

Built with ❤️ using:
- [Streamlit](https://streamlit.io/) - Web framework
- [FAISS](https://github.com/facebookresearch/faiss) - Vector search
- [Google AI](https://ai.google.dev/) - LLM API
- [Sentence-Transformers](https://www.sbert.net/) - `all-MiniLM-L6-v2` embeddings
- [LangChain](https://python.langchain.com/) - Text splitting

---

## 📧 Contact

- **Email:** harishsingla89@gmail.com
- **Project Issues:** Create a GitHub issue

---

**Made with 🌿 for a smarter, greener AI future.**
