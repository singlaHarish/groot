import streamlit as st

def render_connectors():
    sec3_html = (
        '<div class="glass-card" id="connectors">'
        '<div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.5rem;">'
        '<span style="font-size: 2rem;">🔌</span>'
        '<h2 style="margin: 0; color: #aed581; font-size: 1.8rem; font-weight: 800;">2. Enterprise Data Connectors</h2>'
        '</div>'
        '<p style="color: #b0bec5; font-size: 1rem; margin-bottom: 1.5rem;">'
        'Groot seamlessly ingests, cleans, and pre-filters massive heterogeneous enterprise data pipelines prior to LLM inference:'
        '</p>'
        '<div class="tech-grid">'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">📄</div><div class="tech-step-content"><h4>PDF & Document Reports</h4><p>Parses complex multi-page PDF manuals, financial statements, and technical specifications with table extraction.</p></div></div>'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">🖼️</div><div class="tech-step-content"><h4>OCR & Image Pipelines</h4><p>Extracts structured text from scanned documents, diagrams, blueprints, and handwritten operational records.</p></div></div>'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">📚</div><div class="tech-step-content"><h4>100+ Document Batches</h4><p>Bulk indexes large document archives (100+ files / GB scale) in parallel vector search spaces with high throughput.</p></div></div>'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">📘</div><div class="tech-step-content"><h4>Confluence Knowledge Base</h4><p>Direct API integration for live internal wiki pages, team documentation, and technical architecture guides.</p></div></div>'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">📁</div><div class="tech-step-content"><h4>Microsoft SharePoint</h4><p>Syncs enterprise cloud file repositories, shared team drives, and corporate policy stores securely.</p></div></div>'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">⚡</div><div class="tech-step-content"><h4>dbUnity & SQL Databases</h4><p>Connects to relational and NoSQL databases to vectorize structured records, schema docs, and transaction logs.</p></div></div>'
        '</div></div>'
    )
    st.markdown(sec3_html, unsafe_allow_html=True)
