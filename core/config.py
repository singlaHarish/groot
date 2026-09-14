import os
import sys

def is_streamlit_context() -> bool:
    """Check if execution is running inside Streamlit context."""
    try:
        import streamlit as st
        _ = st.session_state
        return True
    except (ImportError, AttributeError, RuntimeError):
        return False

def streamlit_cache(func):
    """Decorator that applies Streamlit caching only if in Streamlit context."""
    if is_streamlit_context():
        import streamlit as st
        return st.cache_resource(show_spinner=f"Loading {func.__name__}...")(func)
    return func

def configure_environment():
    """Configure runtime environment flags for thread safety and performance."""
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    try:
        import torch
        torch.set_num_threads(max(1, torch.get_num_threads()))
    except ImportError:
        pass
