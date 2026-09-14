"""
Groot MCP Server — Path A (stdio transport)
============================================
Exposes Groot's retrieval pipeline as an MCP tool that any MCP-compatible
client (Kiro, VS Code GitHub Copilot, Claude Desktop, etc.) can call.

Transport : stdio  (JSON-RPC, one message per line)
Tools     : retrieve_context, index_document, list_indexed

Usage
-----
The server is launched automatically by the MCP client using the config
in .kiro/settings/mcp.json (Kiro) or .vscode/mcp.json (VS Code).
You do not run this file manually.

If you want to test it manually:
    python mcp_server.py
    # then type JSON-RPC messages and press Enter
"""

import sys
import json
import logging
import os
import io
import time

# MCP uses stdout for JSON-RPC messages, so diagnostics must use a separate
# stream. The log location can be overridden for VS Code or local debugging.
_DEFAULT_LOG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    ".groot_cache",
    "mcp_server.log",
)
_logger = logging.getLogger("groot.mcp")


def configure_logging() -> None:
    log_target = os.environ.get("GROOT_MCP_LOG", _DEFAULT_LOG_PATH)
    if log_target.lower() == "stderr":
        handler = logging.StreamHandler(sys.stderr)
    else:
        os.makedirs(os.path.dirname(os.path.abspath(log_target)), exist_ok=True)
        handler = logging.FileHandler(log_target, encoding="utf-8")

    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    ))
    _logger.setLevel(logging.INFO)
    _logger.addHandler(handler)
    _logger.propagate = False


# ── In-process document cache ──────────────────────────────────────────────
# Stores already-indexed documents so repeated queries on the same file
# don't re-embed everything from scratch.
# Key: absolute pdf path  Value: { full_text, chunks, index }
_cache: dict = {}


# ── JSON-RPC helpers ────────────────────────────────────────────────────────

def send(obj: dict) -> None:
    """Write a JSON-RPC message to stdout."""
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def ok(rid, result: dict) -> None:
    send({"jsonrpc": "2.0", "id": rid, "result": result})


def err(rid, code: int, message: str) -> None:
    send({"jsonrpc": "2.0", "id": rid,
          "error": {"code": code, "message": message}})


# ── Tool definitions ────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "retrieve_context",
        "description": (
            "Given a path to a PDF file and a natural-language query, "
            "extracts the most relevant sections from the document using "
            "vector search and keyword re-ranking. "
            "Returns an optimized excerpt — typically 3–8% of the full "
            "document's tokens — ready to use as LLM context. "
            "Use this instead of reading the entire file when answering "
            "questions about a large document."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pdf_path": {
                    "type": "string",
                    "description": "Absolute path to the PDF file on disk."
                },
                "query": {
                    "type": "string",
                    "description": "The question or topic to retrieve context for."
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of chunks to return (default 8).",
                    "default": 8
                }
            },
            "required": ["pdf_path", "query"]
        }
    },
    {
        "name": "index_document",
        "description": (
            "Pre-indexes a PDF file so that subsequent retrieve_context "
            "calls on the same file are instant. "
            "Call this once when you load a document. "
            "Returns a summary: page count, chunk count, token count."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pdf_path": {
                    "type": "string",
                    "description": "Absolute path to the PDF file on disk."
                },
                "chunk_size": {
                    "type": "integer",
                    "description": "Words per chunk (default 500).",
                    "default": 500
                },
                "chunk_overlap": {
                    "type": "integer",
                    "description": "Overlap between chunks in words (default 100).",
                    "default": 100
                }
            },
            "required": ["pdf_path"]
        }
    },
    {
        "name": "list_indexed",
        "description": (
            "Lists all PDF files that have been indexed in the current session, "
            "with their chunk count and token count."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "prepare_comparison_data",
        "description": (
            "Prepare data for quality comparison: extracts full document text and "
            "retrieves optimized chunks for a query. Returns both texts ready for "
            "you to generate responses. No API key needed — you generate responses "
            "using your own LLM, then call compare_responses to measure quality."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pdf_path": {
                    "type": "string",
                    "description": "Absolute path to the PDF file on disk."
                },
                "query": {
                    "type": "string",
                    "description": "The question or topic to retrieve optimized chunks for."
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of retrieved chunks to return (default 8).",
                    "default": 8
                },
                "chunk_size": {
                    "type": "integer",
                    "description": "Words per chunk (default 500).",
                    "default": 500
                },
                "chunk_overlap": {
                    "type": "integer",
                    "description": "Overlap between chunks in words (default 100).",
                    "default": 100
                }
            },
            "required": ["pdf_path", "query"]
        }
    },
    {
        "name": "compare_responses",
        "description": (
            "Compare quality between two LLM responses using semantic similarity. "
            "Measures F1 score, precision, and recall to show how well the optimized "
            "response matches the full-document response. Lightweight — no API key needed."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "full_response": {
                    "type": "string",
                    "description": "Response generated from full document context."
                },
                "optimized_response": {
                    "type": "string",
                    "description": "Response generated from Groot-optimized chunks."
                }
            },
            "required": ["full_response", "optimized_response"]
        }
    },
    {
        "name": "quality_analysis",
        "description": (
            "One-shot quality analysis: retrieves document data, measures efficiency, "
            "and compares response quality. Provide PDF, query, and both responses. "
            "Returns complete report with token reduction %, F1 score, precision, recall, "
            "and quality assessment — everything in one call."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pdf_path": {
                    "type": "string",
                    "description": "Absolute path to the PDF file on disk."
                },
                "query": {
                    "type": "string",
                    "description": "The question or topic used for the comparison."
                },
                "full_response": {
                    "type": "string",
                    "description": "Response generated from full document context."
                },
                "optimized_response": {
                    "type": "string",
                    "description": "Response generated from Groot-optimized chunks."
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of chunks retrieved (default 8).",
                    "default": 8
                }
            },
            "required": ["pdf_path", "query", "full_response", "optimized_response"]
        }
    }
]


# ── Core logic ──────────────────────────────────────────────────────────────

def _ensure_indexed(pdf_path: str,
                    chunk_size: int = 500,
                    chunk_overlap: int = 100) -> dict:
    """
    Returns the cached index entry for pdf_path, building it if needed.
    Raises FileNotFoundError or RuntimeError on failure.
    """
    abs_path = os.path.abspath(pdf_path)

    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"File not found: {abs_path}")

    # Import here so startup is fast even if heavy deps are slow to load
    import utils  # Groot's own pipeline

    # 1. Check in-process memory cache
    if abs_path in _cache and _cache[abs_path].get("chunk_size") == chunk_size and _cache[abs_path].get("chunk_overlap") == chunk_overlap:
        return _cache[abs_path]

    # 2. Check disk-backed persistent cache
    persistent_entry = utils.load_persistent_index(abs_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if persistent_entry is not None:
        _cache[abs_path] = persistent_entry
        return persistent_entry

    # 3. If not cached, perform full extraction, chunking, and embedding
    with open(abs_path, "rb") as f:
        full_text = utils.extract_text_from_pdf(f)

    if not full_text.strip():
        raise RuntimeError("Could not extract text from PDF. "
                           "Ensure the file is text-based, not a scanned image.")

    chunks = utils.chunk_text(full_text,
                              chunk_size=chunk_size,
                              chunk_overlap=chunk_overlap)

    index, _ = utils.build_faiss_index(chunks, api_key=None, show_progress=False)
    token_count = utils.count_tokens(full_text)

    # Save to disk persistent cache
    utils.save_persistent_index(
        pdf_path=abs_path,
        full_text=full_text,
        chunks=chunks,
        index=index,
        token_count=token_count,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    entry = {
        "full_text":    full_text,
        "chunks":       chunks,
        "index":        index,
        "chunk_size":   chunk_size,
        "chunk_overlap": chunk_overlap,
        "token_count":  token_count,
        "path":         abs_path,
    }
    _cache[abs_path] = entry
    return entry


def tool_retrieve_context(args: dict) -> str:
    import utils

    pdf_path = args["pdf_path"]
    query    = args["query"]
    top_k    = int(args.get("top_k", 8))

    entry    = _ensure_indexed(pdf_path)
    retrieved = utils.search_chunks(
        query, entry["index"], entry["chunks"],
        api_key=None, top_k=top_k
    )

    optimized_text   = "\n\n---\n\n".join(retrieved)
    original_tokens  = entry["token_count"]
    optimized_tokens = utils.count_tokens(optimized_text)
    savings          = round(100 * (1 - optimized_tokens / original_tokens), 1)

    header = (
        f"[Groot] {len(retrieved)} chunks retrieved from "
        f"'{os.path.basename(pdf_path)}'\n"
        f"Tokens: {optimized_tokens:,} (vs {original_tokens:,} full doc) "
        f"— {savings}% reduction\n"
        f"{'─' * 60}\n\n"
    )
    return header + optimized_text


def tool_index_document(args: dict) -> str:
    import utils

    pdf_path     = args["pdf_path"]
    chunk_size   = int(args.get("chunk_size", 500))
    chunk_overlap = int(args.get("chunk_overlap", 100))

    # Force re-index if already cached with different settings
    abs_path = os.path.abspath(pdf_path)
    if abs_path in _cache:
        existing = _cache[abs_path]
        if (existing["chunk_size"] != chunk_size or
                existing["chunk_overlap"] != chunk_overlap):
            del _cache[abs_path]

    entry = _ensure_indexed(pdf_path, chunk_size, chunk_overlap)

    return (
        f"Indexed '{os.path.basename(pdf_path)}'\n"
        f"  Chunks : {len(entry['chunks'])}\n"
        f"  Tokens : {entry['token_count']:,}\n"
        f"  Settings: chunk_size={chunk_size} words, "
        f"overlap={chunk_overlap} words"
    )


def tool_list_indexed(_args: dict) -> str:
    if not _cache:
        return "No documents indexed in this session."
    lines = ["Indexed documents:"]
    for path, entry in _cache.items():
        lines.append(
            f"  • {os.path.basename(path)}"
            f" — {len(entry['chunks'])} chunks"
            f" / {entry['token_count']:,} tokens"
            f"\n    {path}"
        )
    return "\n".join(lines)


def tool_prepare_comparison_data(args: dict) -> str:
    """
    Prepares data for quality comparison: returns full text + optimized chunks.
    No API key needed. You generate responses yourself, then use compare_responses.
    """
    import utils

    pdf_path     = args["pdf_path"]
    query        = args["query"]
    top_k        = int(args.get("top_k", 8))
    chunk_size   = int(args.get("chunk_size", 500))
    chunk_overlap = int(args.get("chunk_overlap", 100))

    # Ensure document is indexed
    entry = _ensure_indexed(pdf_path, chunk_size, chunk_overlap)
    full_text = entry["full_text"]
    chunks = entry["chunks"]
    index = entry["index"]

    # Retrieve optimized chunks
    retrieved = utils.search_chunks(query, index, chunks, api_key=None, top_k=top_k)
    optimized_text = "\n\n---\n\n".join(retrieved)

    # Calculate token counts and savings
    full_tokens = utils.count_tokens(full_text)
    opt_tokens = utils.count_tokens(optimized_text)
    savings_pct = round(100 * (1 - opt_tokens / full_tokens), 1) if full_tokens > 0 else 0

    # Format output
    output = f"""[Groot] Comparison Data Ready
{'─' * 60}

EFFICIENCY (before generating responses):
  Token Reduction Potential: {savings_pct}%
  Full Document Size: {full_tokens:,} tokens
  Optimized Context Size: {opt_tokens:,} tokens
  Chunks Retrieved: {len(retrieved)}

{'─' * 60}
FULL DOCUMENT TEXT:
(Use this to generate response #1 with your LLM)

{full_text}

{'─' * 60}
OPTIMIZED CHUNKS:
(Use this to generate response #2 with your LLM)

{optimized_text}

{'─' * 60}
NEXT STEPS:
1. Generate response #1 by prompting your LLM with the FULL DOCUMENT TEXT above
2. Generate response #2 by prompting your LLM with the OPTIMIZED CHUNKS above
3. Use the compare_responses tool to measure quality (F1 score, precision, recall)
"""

    return output


def tool_compare_responses(args: dict) -> str:
    """
    Compare quality between two responses using semantic similarity.
    Returns F1 score, precision, recall, and quality label.
    """
    import utils

    full_response = args["full_response"]
    optimized_response = args["optimized_response"]

    # Compute quality metrics
    quality = utils.compute_response_quality(full_response, optimized_response)

    # Format output
    output = f"""[Groot] Response Quality Comparison
{'─' * 60}

QUALITY METRICS:
  F1 Score (semantic match): {quality['f1']:.1%}
  Precision (relevance): {quality['precision']:.1%}
  Recall (coverage): {quality['recall']:.1%}
  Quality Label: {quality['quality_label']}
  Description: {quality['description']}

{'─' * 60}
QUALITY ASSESSMENT:
{quality['description']}

The optimized response captures {quality['recall']:.0%} of the key information 
from the full response with {quality['precision']:.0%} relevance.
F1 score of {quality['f1']:.1%} indicates {quality['quality_label'].lower()}.
"""

    return output


def tool_quality_analysis(args: dict) -> str:
    """
    One-shot quality analysis: retrieves data, measures efficiency, and compares responses.
    Returns complete report with efficiency metrics and quality assessment.
    """
    import utils

    pdf_path     = args["pdf_path"]
    query        = args["query"]
    full_response = args["full_response"]
    optimized_response = args["optimized_response"]
    top_k        = int(args.get("top_k", 8))

    # Prepare comparison data (retrieves full text + optimized chunks)
    entry = _ensure_indexed(pdf_path)
    full_text = entry["full_text"]
    chunks = entry["chunks"]
    index = entry["index"]

    # Calculate token counts and savings
    full_tokens = utils.count_tokens(full_text)
    
    # Retrieve optimized chunks
    retrieved = utils.search_chunks(query, index, chunks, api_key=None, top_k=top_k)
    optimized_text = "\n\n---\n\n".join(retrieved)
    opt_tokens = utils.count_tokens(optimized_text)
    savings_pct = round(100 * (1 - opt_tokens / full_tokens), 1) if full_tokens > 0 else 0

    # Compute quality metrics
    quality = utils.compute_response_quality(full_response, optimized_response)

    # Format complete report
    output = f"""[Groot] Complete Quality Analysis Report
{'═' * 60}

EFFICIENCY METRICS:
  Token Reduction: {savings_pct}%
  Full Document: {full_tokens:,} tokens
  Optimized Context: {opt_tokens:,} tokens
  Chunks Retrieved: {len(retrieved)}

QUALITY METRICS:
  F1 Score (semantic match): {quality['f1']:.1%}
  Precision (relevance): {quality['precision']:.1%}
  Recall (coverage): {quality['recall']:.1%}
  Quality Label: {quality['quality_label']}

{'─' * 60}
FULL DOCUMENT RESPONSE:
{full_response}

{'─' * 60}
OPTIMIZED RESPONSE:
{optimized_response}

{'─' * 60}
ANALYSIS SUMMARY:

Efficiency: The optimized context is {savings_pct}% smaller than the full document.

Quality: {quality['description']}
         The optimized response captures {quality['recall']:.0%} of the key information
         from the full response with {quality['precision']:.0%} relevance.

Recommendation: {'✅ EXCELLENT — Quality is maintained with significant savings!' if quality['f1'] >= 0.85 else '✅ GOOD — Quality is well-preserved with significant savings.' if quality['f1'] >= 0.70 else '⚠️ FAIR — Notable quality loss but still useful.' if quality['f1'] >= 0.50 else '❌ POOR — Significant quality degradation.'}
{'═' * 60}
"""

    return output


# ── Request dispatcher ──────────────────────────────────────────────────────

def handle(request: dict) -> None:
    method = request.get("method", "")
    rid    = request.get("id")          # None for notifications
    _logger.info("request id=%r method=%s", rid, method)

    # ── Lifecycle ──────────────────────────────────────────────────────────
    if method == "initialize":
        ok(rid, {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "groot", "version": "1.0.0"},
            "capabilities": {"tools": {}}
        })
        _logger.info("initialized id=%r", rid)

    elif method == "notifications/initialized":
        _logger.info("client initialization notification received")

    elif method == "ping":
        ok(rid, {})
        _logger.info("ping completed id=%r", rid)

    # ── Tool discovery ─────────────────────────────────────────────────────
    elif method == "tools/list":
        ok(rid, {"tools": TOOLS})
        _logger.info("listed %d tools id=%r", len(TOOLS), rid)

    # ── Tool execution ─────────────────────────────────────────────────────
    elif method == "tools/call":
        params    = request.get("params", {})
        tool_name = params.get("name", "")
        args      = params.get("arguments", {})
        started = time.perf_counter()
        _logger.info(
            "tool started id=%r tool=%s argument_keys=%s",
            rid, tool_name, sorted(args) if isinstance(args, dict) else [],
        )

        try:
            if tool_name == "retrieve_context":
                text = tool_retrieve_context(args)
            elif tool_name == "index_document":
                text = tool_index_document(args)
            elif tool_name == "list_indexed":
                text = tool_list_indexed(args)
            elif tool_name == "prepare_comparison_data":
                text = tool_prepare_comparison_data(args)
            elif tool_name == "compare_responses":
                text = tool_compare_responses(args)
            elif tool_name == "quality_analysis":
                text = tool_quality_analysis(args)
            else:
                err(rid, -32601, f"Unknown tool: {tool_name}")
                return

            ok(rid, {
                "content": [{"type": "text", "text": text}],
                "isError": False
            })
            _logger.info(
                "tool completed id=%r tool=%s duration_ms=%.1f",
                rid, tool_name, (time.perf_counter() - started) * 1000,
            )

        except (FileNotFoundError, RuntimeError) as e:
            _logger.exception("tool failed id=%r tool=%s", rid, tool_name)
            ok(rid, {
                "content": [{"type": "text", "text": f"Error: {e}"}],
                "isError": True
            })
        except Exception as e:
            _logger.exception("tool failed unexpectedly id=%r tool=%s", rid, tool_name)
            ok(rid, {
                "content": [{"type": "text", "text": f"Unexpected error: {e}"}],
                "isError": True
            })

    # ── Unknown method ─────────────────────────────────────────────────────
    elif rid is not None:
        _logger.warning("unknown method id=%r method=%s", rid, method)
        err(rid, -32601, f"Method not found: {method}")


# ── Entry point ─────────────────────────────────────────────────────────────

def main() -> None:
    configure_logging()
    _logger.info("Groot MCP server started pid=%d", os.getpid())

    # Ensure the groot directory is on sys.path so `import utils` works
    # regardless of where the MCP client launches the process from.
    groot_dir = os.path.dirname(os.path.abspath(__file__))
    if groot_dir not in sys.path:
        sys.path.insert(0, groot_dir)

    # Read stdin line by line — one JSON-RPC message per line
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            request = json.loads(raw)
            handle(request)
        except json.JSONDecodeError as e:
            _logger.warning("ignored malformed JSON-RPC input: %s", e)

    _logger.info("Groot MCP server stdin closed; shutting down")


if __name__ == "__main__":
    main()
