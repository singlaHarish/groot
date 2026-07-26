import streamlit as st
import base64

def render_header():
    # Detect navigation query parameters
    query_params = st.query_params
    if "nav" in query_params:
        target = query_params["nav"]
        st.query_params.clear()
        if target == "optimizer":
            st.session_state.page = "optimizer"
        else:
            st.session_state.page = "landing"
            st.session_state.scroll_target = target
        st.rerun()

    # Load logo as base64 for embedding in header link
    try:
        with open("image/groot-logo.png", "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        logo_img_html = f'<img src="data:image/png;base64,{logo_b64}" style="height: 36px; width: 36px; object-fit: contain;">'
    except Exception:
        logo_img_html = '<span>🌿</span>'

    # Render Header layout with Brand, Desktop Links, Launch CTA, and Mobile Hamburger Drawer
    header_html = f"""<div class="header-nav-container" style="display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 0.2rem 0;"><a href="?nav=landing" target="_self" style="font-size: 1.4rem; font-weight: 800; color: #aed581; text-decoration: none; display: flex; align-items: center; gap: 0.5rem;">{logo_img_html} <span>GROOT</span></a><div class="desktop-nav-links" style="display: flex; align-items: center; gap: 1.2rem; font-weight: 600; font-size: 0.9rem;"><a href="?nav=benefits" target="_self" class="nav-text-link">Benefits & ROI</a><a href="?nav=connectors" target="_self" class="nav-text-link">Enterprise Sources</a><a href="?nav=integration" target="_self" class="nav-text-link">Integration</a><a href="?nav=environment" target="_self" class="nav-text-link">Environmental Impact</a><a href="?nav=how-it-works" target="_self" class="nav-text-link">Core Technology</a></div><div style="display: flex; align-items: center; gap: 0.8rem;"><a href="?nav=optimizer" target="_self" class="header-launch-btn">🚀 Launch Optimizer</a><div class="mobile-hamburger-wrapper"><input type="checkbox" id="mobile-drawer-toggle" class="drawer-checkbox"><label for="mobile-drawer-toggle" class="hamburger-icon-btn"><span></span><span></span><span></span></label><div class="mobile-drawer-overlay"><div class="mobile-drawer-content"><div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 0.8rem; border-bottom: 1px solid rgba(156, 204, 101, 0.2);"><div style="display: flex; align-items: center; gap: 0.5rem; color: #aed581; font-weight: 800; font-size: 1.2rem;">{logo_img_html} GROOT Navigation</div><label for="mobile-drawer-toggle" style="color: #b0bec5; font-size: 1.5rem; cursor: pointer; font-weight: bold;">✕</label></div><div style="display: flex; flex-direction: column; gap: 1rem; font-weight: 600;"><a href="?nav=benefits" target="_self" class="drawer-nav-item">💰 Benefits & ROI</a><a href="?nav=connectors" target="_self" class="drawer-nav-item">🔌 Enterprise Sources</a><a href="?nav=integration" target="_self" class="drawer-nav-item">⚡ Integration Pipelines</a><a href="?nav=environment" target="_self" class="drawer-nav-item">🌱 Environmental Impact</a><a href="?nav=how-it-works" target="_self" class="drawer-nav-item">🔬 Core Technology</a><hr style="border-color: rgba(156, 204, 101, 0.2); margin: 0.5rem 0;"><a href="?nav=optimizer" target="_self" class="drawer-launch-item">🚀 Launch Groot Optimizer</a></div></div></div></div></div></div><hr style="margin: 0.8rem 0 1.5rem 0; border-color: rgba(156, 204, 101, 0.2);">"""
    st.markdown(header_html, unsafe_allow_html=True)
