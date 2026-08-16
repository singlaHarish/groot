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
import os
import io

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

    if abs_path in _cache:
        return _cache[abs_path]

    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"File not found: {abs_path}")

    # Import here so startup is fast even if heavy deps are slow to load
    import utils  # Groot's own pipeline

    with open(abs_path, "rb") as f:
        full_text = utils.extract_text_from_pdf(f)

    if not full_text.strip():
        raise RuntimeError("Could not extract text from PDF. "
                           "Ensure the file is text-based, not a scanned image.")

    chunks = utils.chunk_text(full_text,
                              chunk_size=chunk_size,
                              chunk_overlap=chunk_overlap)

    index, _ = utils.build_faiss_index(chunks, api_key=None, show_progress=False)

    entry = {
        "full_text":    full_text,
        "chunks":       chunks,
        "index":        index,
        "chunk_size":   chunk_size,
        "chunk_overlap": chunk_overlap,
        "token_count":  utils.count_tokens(full_text),
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


# ── Request dispatcher ──────────────────────────────────────────────────────

def handle(request: dict) -> None:
    method = request.get("method", "")
    rid    = request.get("id")          # None for notifications

    # ── Lifecycle ──────────────────────────────────────────────────────────
    if method == "initialize":
        ok(rid, {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "groot", "version": "1.0.0"},
            "capabilities": {"tools": {}}
        })

    elif method == "notifications/initialized":
        pass  # notification — no response

    elif method == "ping":
        ok(rid, {})

    # ── Tool discovery ─────────────────────────────────────────────────────
    elif method == "tools/list":
        ok(rid, {"tools": TOOLS})

    # ── Tool execution ─────────────────────────────────────────────────────
    elif method == "tools/call":
        params    = request.get("params", {})
        tool_name = params.get("name", "")
        args      = params.get("arguments", {})

        try:
            if tool_name == "retrieve_context":
                text = tool_retrieve_context(args)
            elif tool_name == "index_document":
                text = tool_index_document(args)
            elif tool_name == "list_indexed":
                text = tool_list_indexed(args)
            else:
                err(rid, -32601, f"Unknown tool: {tool_name}")
                return

            ok(rid, {
                "content": [{"type": "text", "text": text}],
                "isError": False
            })

        except (FileNotFoundError, RuntimeError) as e:
            ok(rid, {
                "content": [{"type": "text", "text": f"Error: {e}"}],
                "isError": True
            })
        except Exception as e:
            ok(rid, {
                "content": [{"type": "text", "text": f"Unexpected error: {e}"}],
                "isError": True
            })

    # ── Unknown method ─────────────────────────────────────────────────────
    elif rid is not None:
        err(rid, -32601, f"Method not found: {method}")


# ── Entry point ─────────────────────────────────────────────────────────────

def main() -> None:
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
        except json.JSONDecodeError:
            pass  # malformed input — MCP spec says ignore


if __name__ == "__main__":
    main()
