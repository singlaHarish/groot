import streamlit as st
import base64

def render_hero():
    try:
        with open("image/groot-logo.png", "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        logo_img_html = f'<img src="data:image/png;base64,{logo_b64}" style="height: 64px; width: 64px; object-fit: contain; vertical-align: middle; margin-right: 0.8rem;">'
    except Exception:
        logo_img_html = '<span style="margin-right: 0.5rem;">🌿</span>'

    st.markdown(f"""
        <div class="hero-container">
            <h1 class="hero-title" style="display: flex; align-items: center; justify-content: center;">
                {logo_img_html}<span>GROOT</span>
            </h1>
            <h2 class="hero-subtitle"><span>G</span>reat <span>R</span>eduction <span>o</span>f <span>o</span>verused <span>T</span>okens</h2>
            <p class="hero-description">
                Slash your enterprise AI costs, latency, and environmental impact instantly. Groot uses high-precision Vector Search Pre-filtering 
                to eliminate redundant data and feed Large Language Models <b>only</b> the context they actually need.
            </p>
        </div>
    """, unsafe_allow_html=True)
    st.write("<br>", unsafe_allow_html=True)
