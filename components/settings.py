import streamlit as st

@st.dialog("⚙️ Configuration & Model Settings")
def render_settings_dialog():
    current = get_settings()
    
    # Backend selection
    default_idx = 1 if current["backend"] == "Vertex AI (Cloud Run)" else 0
    backend = st.radio("Gemini Backend", ["API Key (Local)", "Vertex AI (Cloud Run)"], index=default_idx, key="dlg_backend")
    
    # API Key input (only show for Local mode)
    if backend == "API Key (Local)":
        api_key = st.text_input("Gemini API Key", value=current.get("api_key", "") if current.get("api_key") != "VERTEX_AI_MODE" else "", type="password", help="Get this from Google AI Studio", key="dlg_api_key")
    else:
        api_key = "VERTEX_AI_MODE"
        st.info("Using Vertex AI via Workload Identity")
        
    st.markdown("---")
    
    # Other settings
    cost_per_1m_tokens = st.number_input("LLM Cost per 1M Input Tokens ($)", value=current.get("cost_per_1m", 3.50), step=0.10, key="dlg_cost")
    chunk_size = st.number_input("Chunk Size (Words)", value=current.get("chunk_size", 300), step=50, key="dlg_chunk")
    chunk_overlap = st.number_input("Chunk Overlap (Words)", value=current.get("chunk_overlap", 50), step=10, key="dlg_overlap")
    top_k = st.slider("Top K Chunks", min_value=1, max_value=20, value=current.get("top_k", 5), key="dlg_topk")

    st.markdown("---")
    
    # Save button at the bottom
    if st.button("💾 Save & Apply Settings", key="save_settings_btn", type="primary", use_container_width=True):
        st.session_state.settings_config = {
            "backend": backend,
            "api_key": api_key,
            "cost_per_1m": cost_per_1m_tokens,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "top_k": top_k
        }
        st.rerun()

def get_settings():
    # Initialize default settings state if not present
    if "settings_config" not in st.session_state:
        st.session_state.settings_config = {
            "backend": "Vertex AI (Cloud Run)",
            "api_key": "VERTEX_AI_MODE",
            "cost_per_1m": 3.50,
            "chunk_size": 300,
            "chunk_overlap": 50,
            "top_k": 5
        }
    return st.session_state.settings_config

# Alias for backwards compatibility
render_settings_popover = render_settings_dialog

