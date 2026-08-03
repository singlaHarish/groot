import streamlit as st
from PIL import Image
import utils
from components.settings import render_settings_dialog, get_settings

from components.header import render_header

def render_optimizer():
    # Identical Top Navbar Header as Landing Page
    render_header()
    
    # Retrieve current active settings configuration
    config = get_settings()
    
    # Optimizer Action Bar (Back to Landing Page & Settings Modal Trigger)
    sub_col1, sub_col2 = st.columns([0.7, 0.3], vertical_alignment="center")
    
    with sub_col1:
        if st.button("← Back to Landing Page", key="optimizer_back_btn"):
            st.session_state.page = "landing"
            st.rerun()
            
    with sub_col2:
        if st.button("⚙️ Settings", key="open_settings_btn", width="stretch"):
            render_settings_dialog()

    st.markdown("<hr style='margin: 0.8rem 0 1.5rem 0; border-color: rgba(156, 204, 101, 0.2);'>", unsafe_allow_html=True)

    # --- SECTION 1: DOCUMENT INPUT & QUERY ---
    st.markdown("""
        <div class="glass-card">
            <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.4rem;">
                <span style="font-size: 1.8rem;">📄</span>
                <h3 style="margin: 0; color: #aed581; font-weight: 800;">1. Upload Document & Enter Search Query</h3>
            </div>
            <p style="color: #b0bec5; font-size: 1.05rem; margin-top: 0; margin-bottom: 1.2rem;">
                This interactive demo demonstrates how your raw document is chunked, vectorized, and token-optimized.
            </p>
    """, unsafe_allow_html=True)

    col_upload, col_query = st.columns(2)

    with col_upload:
        uploaded_file = st.file_uploader("Upload Document (PDF)", type=["pdf"])

    with col_query:
        query = st.text_input("Enter Search Query / Prompt (Press Enter to Run):", placeholder="e.g. Summarize the main risk factors...", key="optimizer_query_input")
        generate_btn = st.button("⚡ Optimize and Compare", width="stretch")

    st.markdown("</div>", unsafe_allow_html=True)

    # Validation check if file uploaded but search query is empty
    if uploaded_file and not query.strip():
        if generate_btn:
            st.error("⚠️ **Action Required:** Please enter a search query or prompt into the search input box below.")
            st.markdown("""
                <style>
                div[data-testid="stTextInput"] input {
                    border: 2px solid #ef5350 !important;
                    background-color: rgba(239, 83, 80, 0.15) !important;
                    box-shadow: 0 0 15px rgba(239, 83, 80, 0.5) !important;
                    animation: pulse-border 1.5s infinite;
                }
                @keyframes pulse-border {
                    0% { box-shadow: 0 0 5px rgba(239, 83, 80, 0.4); }
                    50% { box-shadow: 0 0 20px rgba(239, 83, 80, 0.8); }
                    100% { box-shadow: 0 0 5px rgba(239, 83, 80, 0.4); }
                }
                </style>
            """, unsafe_allow_html=True)

    if "doc_thread" not in st.session_state:
        st.session_state.doc_thread = None
    if "doc_results" not in st.session_state:
        st.session_state.doc_results = None

    # --- CORE OPTIMIZATION ENGINE ---
    backend = config["backend"]
    api_key = config["api_key"]
    cost_per_1m = config["cost_per_1m"]
    chunk_size = config["chunk_size"]
    chunk_overlap = config["chunk_overlap"]
    top_k = config["top_k"]

    if generate_btn and uploaded_file and query.strip():
        if backend == "API Key (Local)" and not api_key:
            st.error("Please click ⚙️ Settings in the top header and enter your Gemini API Key.")
            st.stop()
            
        st.session_state.doc_results = None
        
        # Load models in main thread before starting background thread
        utils.get_embedding_model()
        utils.get_encoder()
        
        thread = utils.DocumentProcessorThread(uploaded_file.getvalue(), chunk_size, chunk_overlap, api_key)
        thread.start()
        st.session_state.doc_thread = thread

    if st.session_state.doc_thread is not None:
        thread = st.session_state.doc_thread
        if not thread.is_done:
            st.progress(thread.progress_pct, text=thread.progress_msg)
            import time
            time.sleep(1)
            st.rerun()
        else:
            st.session_state.doc_thread = None
            if thread.error:
                st.error(thread.error)
            else:
                st.session_state.doc_results = {
                    "full_text": thread.result_full_text,
                    "chunks": thread.result_chunks,
                    "index": thread.result_index,
                    "embeddings": thread.result_embeddings
                }

    if st.session_state.doc_results and query.strip():
        full_text = st.session_state.doc_results["full_text"]
        chunks = st.session_state.doc_results["chunks"]
        index = st.session_state.doc_results["index"]
        
        unoptimized_tokens = utils.count_tokens(full_text)
        unoptimized_cost = (unoptimized_tokens / 1_000_000) * cost_per_1m

        with st.spinner("Executing vector search retrieval..."):
            retrieved_chunks = utils.search_chunks(query, index, chunks, api_key, top_k=int(top_k))
            optimized_text = "\n\n---\n\n".join(retrieved_chunks)
            optimized_tokens = utils.count_tokens(optimized_text)
            optimized_cost = (optimized_tokens / 1_000_000) * cost_per_1m
            savings_pct = 100 * (1 - (optimized_tokens / unoptimized_tokens)) if unoptimized_tokens > 0 else 0

        st.write("<br>", unsafe_allow_html=True)

        # --- SECTION 2: METRICS & TOKEN SAVINGS COMPARISON ---
        st.markdown("""
            <div class="glass-card">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem; margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.8rem;">
                        <span style="font-size: 1.8rem;">📊</span>
                        <h3 style="margin: 0; color: #aed581; font-weight: 800;">2. Token Reduction & Cost Impact</h3>
                    </div>
                    <div style="background: rgba(156, 204, 101, 0.15); border: 1px solid #9ccc65; padding: 4px 14px; border-radius: 16px; color: #aed581; font-weight: 700; font-size: 0.9rem;">
                        Sub-Millisecond Vector Retrieval
                    </div>
                </div>
        """, unsafe_allow_html=True)

        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric("Raw Unoptimized Context", f"{unoptimized_tokens:,} tokens", f"${unoptimized_cost:.5f}", delta_color="off")
        with m_col2:
            st.metric("Groot Optimized Context", f"{optimized_tokens:,} tokens", f"${optimized_cost:.5f}", delta_color="off")
        with m_col3:
            st.metric("Cost & Token Savings", f"{savings_pct:.1f}%", f"${(unoptimized_cost - optimized_cost):.5f} saved!", delta_color="normal")

        st.markdown("</div>", unsafe_allow_html=True)

        st.write("<br>", unsafe_allow_html=True)

        # --- SECTION 3: SIDE-BY-SIDE LLM RESPONSE COMPARISON ---
        st.markdown("""
            <div class="glass-card">
                <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1rem;">
                    <span style="font-size: 1.8rem;">🤖</span>
                    <h3 style="margin: 0; color: #aed581; font-weight: 800;">3. Side-by-Side Model Response Comparison</h3>
                </div>
        """, unsafe_allow_html=True)

        resp_col1, resp_col2 = st.columns(2)
        
        with resp_col1:
            st.markdown("<h4 style='color: #ef5350;'>Unoptimized Response (Full Raw Document)</h4>", unsafe_allow_html=True)
            with st.spinner("Generating raw document response..."):
                if backend == "API Key (Local)":
                    full_response = utils.generate_gemini_response(api_key, full_text, query)
                else:
                    full_response = utils.generate_gemini_vertex(full_text, query)
                st.info(full_response)
                
        with resp_col2:
            st.markdown("<h4 style='color: #9ccc65;'>Optimized Response (Groot Vector Context)</h4>", unsafe_allow_html=True)
            with st.spinner("Generating Groot optimized response..."):
                if backend == "API Key (Local)":
                    opt_response = utils.generate_gemini_response(api_key, optimized_text, query)
                else:
                    opt_response = utils.generate_gemini_vertex(optimized_text, query)
                st.success(opt_response)

        st.markdown("</div>", unsafe_allow_html=True)
