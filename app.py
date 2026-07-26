import streamlit as st
from components.header import render_header
from sections.hero import render_hero
from sections.technology import render_technology
from sections.cost_savings import render_cost_savings
from sections.connectors import render_connectors
from sections.environment import render_environment
from sections.integration import render_integration
from sections.footer_cta import render_footer_cta
from sections.optimizer import render_optimizer

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Groot", layout="wide", page_icon="image/groot-logo.png")

# --- SESSION STATE INITIALIZATION ---
if "page" not in st.session_state:
    st.session_state.page = "landing"

# --- GLOBAL CUSTOM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        overscroll-behavior: none;
        overflow-x: hidden;
    }

    /* Global Styles - Deep Organic Wood & Forest Theme */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #1c2b19 0%, #121910 40%, #0d120a 100%);
        color: #e2ece9;
        overscroll-behavior: none;
        min-height: 100vh;
    }
    /* Hide Streamlit Chrome & Align Header Flush to Top */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    #MainMenu, footer, div[data-testid="stDecoration"] {
        display: none !important;
    }
    .stMainBlockContainer, [data-testid="stMainBlockContainer"] {
        padding-top: 0.5rem !important;
        margin-top: 0rem !important;
    }
    .stAppViewContainer {
        padding-top: 0rem !important;
    }

    /* Hero Section - Centered & Elegant */
    .hero-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 1.5rem 1rem 1rem 1rem;
        background: linear-gradient(180deg, rgba(46, 125, 50, 0.12) 0%, rgba(0,0,0,0) 100%);
        border-bottom: 1px solid rgba(156, 204, 101, 0.15);
        border-radius: 0 0 20px 20px;
        margin-bottom: 1.5rem;
    }
    
    .hero-badge {
        background: rgba(156, 204, 101, 0.12);
        border: 1px solid #9ccc65;
        color: #aed581;
        padding: 4px 14px;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 0.6rem;
        display: inline-block;
    }

    .hero-title {
        font-size: 3.2rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #aed581 0%, #81c784 40%, #4fc3f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
        letter-spacing: -0.5px;
    }

    .hero-subtitle {
        font-size: 2.2rem !important;
        color: #e1f5fe !important;
        margin-top: -15px !important;
        margin-bottom: 2rem !important;
    }
    
    .hero-subtitle span {
        color: #81c784;
        font-weight: 800;
    }

    .hero-description {
        max-width: 1000px;
        font-size: 1.1rem;
        color: #cfd8dc;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    
    /* Modern Compact Cards */
    .glass-card {
        background: rgba(28, 22, 17, 0.65);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid rgba(156, 204, 101, 0.2);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
        margin-bottom: 1.2rem;
    }

    /* Tech Step & Connector Grid */
    .tech-step {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        background: rgba(255, 255, 255, 0.03);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid #81c784;
    }

    .tech-step-num {
        background: linear-gradient(135deg, #2e7d32, #1b5e20);
        color: #e8f5e9;
        font-weight: 800;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }

    .tech-step-content h4 {
        margin: 0;
        color: #4fc3f7;
        font-size: 1.1rem;
    }
    
    .tech-step-content p {
        margin: 0.3rem 0 0 0;
        font-size: 0.95rem;
        color: #b0bec5;
    }
    /* Enforce Dark Theme Inputs & File Uploaders */
    .stTextInput input, .stTextArea textarea, div[data-testid="stFileUploader"] {
        background-color: rgba(18, 25, 16, 0.85) !important;
        color: #e2ece9 !important;
        border: 1px solid rgba(156, 204, 101, 0.3) !important;
        border-radius: 8px !important;
    }
    div[data-testid="stFileUploader"] section {
        background-color: rgba(18, 25, 16, 0.6) !important;
        border: 1px dashed rgba(156, 204, 101, 0.4) !important;
    }
    div[data-testid="stFileUploader"] section * {
        color: #b0bec5 !important;
    }
    label[data-testid="stWidgetLabel"] {
        color: #aed581 !important;
        font-weight: 700 !important;
    }
    /* Buttons */
    .stButton > button {
        background-color: #2e7d32 !important;
        color: white !important;
        border-radius: 30px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 0.75rem 2rem !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #9ccc65 !important;
        color: #1a1614 !important;
        border: 2px solid #2e7d32 !important;
    }

    /* Clean Header Text Links (Pure HTML Links with Hover Glow) */
    .nav-text-link {
        color: #b0bec5 !important;
        text-decoration: none !important;
        padding: 4px 8px !important;
        border-radius: 6px !important;
        transition: all 0.25s ease-in-out !important;
    }
    .nav-text-link:hover {
        color: #9ccc65 !important;
        background: rgba(156, 204, 101, 0.1) !important;
        text-shadow: 0 0 10px rgba(156, 204, 101, 0.4) !important;
    }

    /* Header Launch CTA Button (Visible on Desktop & Mobile) */
    .header-launch-btn {
        background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%) !important;
        color: #ffffff !important;
        padding: 6px 16px !important;
        border-radius: 20px !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        text-decoration: none !important;
        border: 1px solid #81c784 !important;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.4) !important;
        transition: all 0.3s ease !important;
        white-space: nowrap !important;
        display: inline-flex !important;
        align-items: center !important;
    }
    .header-launch-btn:hover {
        background: linear-gradient(135deg, #9ccc65 0%, #81c784 100%) !important;
        color: #121910 !important;
        box-shadow: 0 6px 18px rgba(156, 204, 101, 0.6) !important;
        transform: translateY(-1px) !important;
    }

    /* Mobile Hamburger & Drawer Menu System */
    .mobile-hamburger-wrapper {
        display: none;
    }
    .drawer-checkbox {
        display: none;
    }
    .hamburger-icon-btn {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        width: 26px;
        height: 20px;
        cursor: pointer;
        z-index: 1001;
    }
    .hamburger-icon-btn span {
        display: block;
        height: 3px;
        width: 100%;
        background-color: #aed581;
        border-radius: 3px;
        transition: all 0.3s ease;
    }
    .mobile-drawer-overlay {
        position: fixed;
        top: 0;
        right: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(8px);
        z-index: 9999;
        display: flex;
        justify-content: flex-end;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
    }
    .mobile-drawer-content {
        width: 280px;
        height: 100%;
        background: #121910;
        border-left: 1px solid rgba(156, 204, 101, 0.3);
        padding: 2rem 1.5rem;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        box-shadow: -10px 0 30px rgba(0,0,0,0.5);
    }
    .drawer-checkbox:checked ~ .mobile-drawer-overlay {
        opacity: 1;
        visibility: visible;
    }
    .drawer-checkbox:checked ~ .mobile-drawer-overlay .mobile-drawer-content {
        transform: translateX(0);
    }
    .drawer-nav-item {
        color: #cfd8dc !important;
        text-decoration: none !important;
        font-size: 1rem !important;
        padding: 0.5rem 0.8rem !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        display: block !important;
    }
    .drawer-nav-item:hover {
        background: rgba(156, 204, 101, 0.15) !important;
        color: #aed581 !important;
    }
    .drawer-launch-item {
        background: linear-gradient(135deg, #2e7d32, #1b5e20) !important;
        color: #ffffff !important;
        text-decoration: none !important;
        padding: 0.8rem !important;
        border-radius: 12px !important;
        text-align: center !important;
        font-weight: 800 !important;
        margin-top: 0.5rem !important;
    }

    /* Tech Step & Section Card Grid System: 3x2 on desktop, 1x6 on mobile */
    .tech-grid {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 1.2rem !important;
    }

    /* Mobile View Adaptations (< 900px) */
    @media (max-width: 900px) {
        .desktop-nav-links {
            display: none !important;
        }
        .mobile-hamburger-wrapper {
            display: block !important;
        }
        .header-nav-container {
            flex-direction: row !important;
            align-items: center !important;
        }
        .tech-grid {
            grid-template-columns: 1fr !important;
        }
        .hero-title {
            font-size: 2.8rem !important;
        }
        .hero-subtitle {
            font-size: 1.3rem !important;
        }
        .hero-description {
            font-size: 1rem !important;
        }
        .glass-card {
            padding: 1.2rem !important;
            margin-bottom: 1rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# --- LANDING PAGE RENDERER ---
def landing_page():
    render_header()
    render_hero()
    render_cost_savings()
    render_connectors()
    render_integration()
    render_environment()
    render_technology()
    render_footer_cta()

    if "scroll_target" in st.session_state and st.session_state.scroll_target:
        target = st.session_state.scroll_target
        st.session_state.scroll_target = None
        st.html(f"""
            <script>
                window.parent.document.getElementById('{target}')?.scrollIntoView({{behavior: 'smooth'}});
            </script>
        """)

# --- APPLICATION ROUTER ---
if st.session_state.page == "landing":
    landing_page()
elif st.session_state.page == "optimizer":
    render_optimizer()
