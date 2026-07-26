import streamlit as st

def render_environment():
    sec_env_html = (
        '<div class="glass-card" id="environment">'
        '<div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.5rem;">'
        '<span style="font-size: 2rem;">🌱</span>'
        '<h2 style="margin: 0; color: #aed581; font-size: 1.8rem; font-weight: 800;">4. Environmental Sustainability</h2>'
        '</div>'
        '<p style="color: #b0bec5; font-size: 1rem; margin-bottom: 1.5rem;">'
        'Every unnecessary token sent to LLM datacenter GPUs consumes electricity and generates carbon emissions. By reducing input token volume by <b>50-90%</b>, Groot actively protects the planet:'
        '</p>'
        '<div class="tech-grid">'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">⚡</div><div class="tech-step-content"><h4>50-90% Energy Reduction</h4><p>Decreases GPU thermal load and power consumption by pre-filtering data before LLM inference engines fire.</p></div></div>'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">🌍</div><div class="tech-step-content"><h4>Lower Carbon Footprint</h4><p>Cuts enterprise AI CO₂ footprint by gigagrams across high-throughput daily prompt and document workloads.</p></div></div>'
        '<div class="tech-step"><div style="font-size: 1.8rem; flex-shrink: 0;">💧</div><div class="tech-step-content"><h4>Data Center Water Conservation</h4><p>Reduces cooling water evaporative consumption in hyperscale cloud server farms by curtailing peak compute duration.</p></div></div>'
        '</div></div>'
    )
    st.markdown(sec_env_html, unsafe_allow_html=True)
    st.write("<br>", unsafe_allow_html=True)
