import tiktoken

_encoder_cache = None

def get_encoder():
    """Load tiktoken encoder with global caching."""
    global _encoder_cache
    if _encoder_cache is not None:
        return _encoder_cache
    
    try:
        _encoder_cache = tiktoken.get_encoding("cl100k_base")
        return _encoder_cache
    except Exception:
        return None

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
