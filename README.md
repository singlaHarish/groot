# Groot - AI Document Context Optimizer

Groot reduces the amount of document context sent to an LLM. It extracts text
from PDFs, splits the text into overlapping chunks, embeds the chunks locally,
retrieves the most relevant chunks for a query, and compares the result with a
full-document response.

Groot is available in two forms:

1. A Streamlit application for interactive upload, retrieval, cost, and quality
   comparisons.
2. A stdio Model Context Protocol (MCP) server for MCP clients such as VS Code
   GitHub Copilot.

## What Groot does

For each PDF and query, Groot can:

- Extract text page by page with `pypdf`.
- Split text into overlapping word-based chunks.
- Generate local `all-MiniLM-L6-v2` embeddings.
- Store embeddings in a FAISS `IndexFlatL2` index.
- Expand queries, search multiple query variants, and deduplicate candidates.
- Re-rank candidates using literal keyword matches.
- Return only the most relevant chunks instead of the complete document.
- Count full and optimized context tokens with `tiktoken`.
- Estimate input-token cost and savings.
- Generate full-document and optimized-context Gemini responses.
- Compare response quality using embedding-based precision, recall, and F1.

The retrieval pipeline is local. Gemini is used only for response generation
when the Streamlit comparison is run.

## Architecture

```text
PDF upload or MCP PDF path
            |
            v
       PDF extraction
            |
            v
  Word chunking with overlap
            |
            v
 Local SentenceTransformer embeddings
            |
            v
        FAISS index
            |
            v
 Query expansion and vector search
            |
            v
 Keyword re-ranking and top-k selection
            |
            +----------------------+
            |                      |
            v                      v
 Full document context       Retrieved context
            |                      |
            +----------+-----------+
                       v
              Gemini responses
                       |
                       v
             Quality and cost metrics
```

### Main modules

- `app.py` - Streamlit entry point, page routing, and global UI configuration.
- `sections/optimizer.py` - Upload, query, background indexing, retrieval,
  model calls, cost metrics, and response-quality display.
- `components/settings.py` - Streamlit settings for backend, API cost,
  chunking, and top-k retrieval.
- `core/ingestion/` - PDF parsing, chunking, and token counting.
- `core/vectorstore/` - Local embedding model, FAISS construction, and
  persistent index storage.
- `core/retrieval/` - Query expansion, keyword extraction, vector search, and
  re-ranking.
- `core/generation/` - Gemini REST API and Vertex AI generation gateways.
- `core/evaluation/` - Semantic comparison of full and optimized responses.
- `core/services/` - Background document-processing thread used by Streamlit.
- `mcp_server.py` - JSON-RPC stdio MCP server.
- `utils.py` - Backward-compatible facade that re-exports core APIs.

## Retrieval pipeline

### Ingestion and indexing

`pypdf` extracts text from every PDF page. The text is split into chunks using
the configured `chunk_size` and `chunk_overlap` values. The default settings
are 500 words per chunk and 100 words of overlap.

The chunks are embedded with the local
`sentence-transformers/all-MiniLM-L6-v2` model and added to a FAISS
`IndexFlatL2` index.

The Streamlit application performs this work in
`DocumentProcessorThread` so the UI can show progress while indexing.

### Retrieval

`search_chunks`:

1. Expands the query into the original query plus relevant sub-queries.
2. Searches FAISS for each query variant.
3. Merges and deduplicates candidates by chunk index.
4. Subtracts a keyword bonus from distances for literal query-keyword matches.
5. Removes candidates above the similarity threshold when possible.
6. Returns the best `top_k` chunks.

The default candidate pool is `top_k * 5`, the keyword bonus is `0.08`, and
the similarity threshold is an L2 distance of `2.0`.

### Persistent cache

The MCP server uses a two-level cache:

1. An in-process cache for repeated requests during one server session.
2. A disk-backed cache under `.groot_cache/` for reuse across server
   restarts.

Persistent indexes are keyed by the PDF path, modification time, file size,
chunk size, and chunk overlap. The cache contains FAISS index files and
metadata including extracted text, chunks, and token counts.

## Streamlit application

### Installation

Groot requires Python 3.11 or later.

```powershell
git clone <repository-url>
cd groot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Run locally

```powershell
streamlit run app.py
```

The application opens at `http://localhost:8501`.

### Streamlit workflow

1. Upload a text-based PDF.
2. Enter a question or prompt.
3. Select **Optimize and Compare**.
4. Groot indexes the PDF and retrieves the relevant chunks.
5. The application displays full and optimized token counts and estimated
   input costs.
6. Gemini generates a response from the full document and another from the
   retrieved context.
7. Groot displays semantic precision, recall, F1, and a quality label.

The application supports two generation backends:

- **API Key (Local)** - Gemini REST API using a Google AI Studio API key.
- **Vertex AI (Cloud Run)** - `google-genai` using Vertex AI credentials.

The API-key backend requires the key to be entered through the Settings dialog.
Do not commit API keys to the repository.

## MCP server

The MCP server uses stdio JSON-RPC. The MCP client starts the Python process
and communicates through stdin/stdout. stdout is reserved for protocol
messages; diagnostics are written to a log file or stderr.

The VS Code configuration is in `.vscode/mcp.json`:

```json
{
  "servers": {
    "groot": {
      "type": "stdio",
      "command": "C:\\path\\to\\groot\\.venv\\Scripts\\python.exe",
      "args": ["mcp_server.py"],
      "cwd": "C:\\path\\to\\groot"
    }
  }
}
```

### MCP tools

`mcp_server.py` exposes these tools:

- `retrieve_context` - Retrieve relevant PDF chunks for a query.
- `index_document` - Pre-index a PDF and report chunk and token counts.
- `list_indexed` - List documents indexed in the current server session.
- `prepare_comparison_data` - Return the full document and optimized context
  for a matched response comparison.
- `compare_responses` - Compare a full-document response with an optimized
  response.
- `quality_analysis` - Run the complete token-efficiency and response-quality
  analysis.

Example MCP tool input:

```json
{
  "pdf_path": "C:\\path\\to\\groot\\resources\\spring-boot-reference.pdf",
  "query": "How does Spring Boot auto-configuration work?",
  "top_k": 8
}
```

### MCP logging

By default, the server writes lifecycle, request, tool, duration, and error
messages to:

```text
.groot_cache/mcp_server.log
```

To send logs to stderr instead, set this environment variable in the MCP
configuration:

```json
"GROOT_MCP_LOG": "stderr"
```

Do not write application logs to stdout because that would corrupt MCP
JSON-RPC communication.

## Configuration

The Streamlit Settings dialog stores configuration in `st.session_state`.

| Setting | Default | Purpose |
| --- | ---: | --- |
| Gemini backend | Vertex AI (Cloud Run) | Select REST API or Vertex AI generation |
| Cost per 1M input tokens | `$3.50` | Used for estimated cost and savings |
| Chunk size | `500` words | Size of each indexed chunk |
| Chunk overlap | `100` words | Shared text between adjacent chunks |
| Top K | `8` | Number of retrieved chunks |

The cost is an estimate based on the configured input-token price. It is not a
billing report and does not include output-token or provider-specific charges.

## Project structure

```text
groot/
├── app.py
├── mcp_server.py
├── utils.py
├── requirements.txt
├── Dockerfile
├── components/
│   ├── header.py
│   └── settings.py
├── sections/
│   ├── optimizer.py
│   └── ...
├── core/
│   ├── config.py
│   ├── ingestion/
│   ├── vectorstore/
│   ├── retrieval/
│   ├── generation/
│   ├── evaluation/
│   └── services/
├── resources/
│   └── sample PDFs
├── tests/
├── docs/
│   ├── groot-core-pipeline.svg
│   └── groot-core-pipeline.drawio
├── .github/workflows/
│   ├── deploy.yml
│   └── uninstall.yml
└── .groot_cache/
    ├── indexes/
    ├── metadata.json
    └── mcp_server.log
```

`.groot_cache/` is generated runtime data. It should not be treated as source
code and should be excluded from version control when appropriate.

## Testing

The repository includes tests for the core pipeline, persistence, quality
scoring, and MCP tool registration.

```powershell
pytest
```

Individual tests can be run with:

```powershell
pytest tests/test_core.py
pytest tests/test_persistence.py
pytest tests/test_quality.py
```

`tests/test_tools.py` is a lightweight script that imports and prints the
registered MCP tools.

## Deployment

The `Dockerfile` runs the Streamlit application on port `8080`:

```powershell
docker build -t groot:latest .
docker run -p 8080:8080 groot:latest
```

The manual GitHub Actions workflow in `.github/workflows/deploy.yml` builds and
pushes an image to Google Artifact Registry, then deploys it to Cloud Run.
Cloud Run uses the Vertex AI generation path and requires the configured
Google Cloud service-account and project secrets.

The MCP server is intended to be launched by an MCP client. It is not the
entry point used by the Dockerized Streamlit deployment.

## Limitations and future work

- PDF ingestion currently targets text-based PDFs; scanned documents require
  OCR before ingestion.
- Retrieval is currently single-document per index request.
- Embeddings and FAISS search are local, but response generation requires a
  configured Gemini backend.
- The quality score measures semantic alignment between two responses; it is
  not a human factuality evaluation.
- Potential extensions include DOCX/HTML ingestion, multi-document
  collections, stronger re-ranking, and a standalone HTTP API.

## Acknowledgments

- [Streamlit](https://streamlit.io/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net/)
- [LangChain text splitters](https://python.langchain.com/)
- [Google Gemini](https://ai.google.dev/)
