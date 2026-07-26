import streamlit as st

def render_footer_cta():
    cta_html = (
        '<div class="glass-card" style="text-align: center; padding: 2.5rem 1.5rem; background: linear-gradient(180deg, rgba(46, 125, 50, 0.25) 0%, rgba(28, 22, 17, 0.8) 100%); border: 1px solid #9ccc65;">'
        '<h3 style="color: #4fc3f7; font-size: 1.6rem; font-weight: 700; margin-bottom: 0.4rem;">Slash every $100 bill down to $10-$50</h3>'
        '<h2 style="color: #aed581; font-size: 2.2rem; font-weight: 800; margin-bottom: 0.5rem;">Ready to Cut Your AI Token Bill by 50-90%?</h2>'
        '<p style="color: #b0bec5; font-size: 1.1rem; margin-bottom: 1.5rem;">Experience sub-millisecond semantic pre-filtering with your enterprise documents now.</p>'
        '</div>'
    )
    st.markdown(cta_html, unsafe_allow_html=True)

    f_col1, f_col2, f_col3 = st.columns([1, 1.5, 1])
    with f_col2:
        if st.button("🚀 Launch Groot Token Optimizer Now", key="footer_launch_btn", width="stretch"):
            st.session_state.page = "optimizer"
            st.rerun()

    st.markdown("""
        <div style="text-align: center; margin-top: 3rem; padding: 1.5rem 0 1rem 0; border-top: 1px solid rgba(156, 204, 101, 0.15); color: #b0bec5; font-size: 0.9rem;">
            <p style="margin: 0 0 0.3rem 0; font-weight: 600;">© Groot — Made with 💚 by <b style="color: #aed581;">Quantum Avengers</b></p>
            <p style="margin: 0; color: #81c784; font-size: 0.85rem;">🌱 Designed and Developed to save money & the environment by reducing compute energy</p>
        </div>
    """, unsafe_allow_html=True)
