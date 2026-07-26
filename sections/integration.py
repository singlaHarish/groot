import streamlit as st

def render_integration():
    sec_int_html = (
        '<div class="glass-card" id="integration">'
        '<div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.5rem;">'
        '<span style="font-size: 2rem;">⚡</span>'
        '<h2 style="margin: 0; color: #aed581; font-size: 1.8rem; font-weight: 800;">3. Enterprise Integration Pipelines</h2>'
        '</div>'
        '<p style="color: #b0bec5; font-size: 1rem; margin-bottom: 1.5rem;">'
        'Groot can be seamlessly integrated into any enterprise AI workload to pre-filter context and maximize cost efficiency:'
        '</p>'
        '<div class="tech-grid">'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">🎯</div><div class="tech-step-content"><h4>LLM Model Fine-Tuning</h4><p>Pre-filters training corpora to eliminate duplicate tokens and redundant text blocks before model fine-tuning.</p></div></div>'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">🔍</div><div class="tech-step-content"><h4>RAG Document Search</h4><p>Retrieves sub-millisecond top K vector chunks across enterprise knowledge bases for retrieval-augmented generation.</p></div></div>'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">💬</div><div class="tech-step-content"><h4>Live Prompt Q&A</h4><p>Compresses attached PDF and doc files on-the-fly for instant zero-latency prompt responses in conversational AI.</p></div></div>'
        '</div></div>'
    )
    st.markdown(sec_int_html, unsafe_allow_html=True)
    st.write("<br>", unsafe_allow_html=True)
