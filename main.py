# main.py
import streamlit as st
import importlib
from PIL import Image
import base64, io

# -------------------- Init --------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

def navigate_to(page):
    st.session_state.current_page = page
    st.rerun()

# -------------------- Router --------------------
def load_page():
    routes = {
        "home": None,
        "visit": ("visitor", "visitor_main"),
        "conference": ("conference_page", "conference_main"),
    }

    page = st.session_state.current_page

    if page == "home":
        render_home()
        return

    try:
        module_name, fn_name = routes[page]
        module = importlib.import_module(module_name)
        getattr(module, fn_name)(navigate_to)
    except Exception as e:
        st.error(f"Error loading page: {e}")

# -------------------- HOME PAGE STYLE LIKE YOUR SCREENSHOT --------------------
def render_home():

    # Load Logo
    logo = Image.open("zodopt.png")
    buf = io.BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    # -------------------- CSS --------------------
    st.markdown("""
    <style>

    /* Full width layout */
    .block-container {
        max-width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Rounded Gradient Banner (Like Screenshot) */
    .top-banner {
        width: 92%;
        margin: 30px auto;
        padding: 35px 55px;
        border-radius: 35px;
        background: linear-gradient(90deg, #1e62ff, #8a2eff);
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
    }

    .banner-title {
        font-size: 42px;
        font-weight: 900;
        letter-spacing: 1px;
    }

    /* Main content wrapper */
    .content-wrapper {
        width: 92%;
        margin: 30px auto;
        padding: 40px;
        background: white;
        border-radius: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
    }

    /* Page section title */
    .section-title {
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 20px;
        color: #222;
    }

    /* Cards container */
    .card-box {
        background: #ffffff;
        padding: 50px 20px;
        border-radius: 25px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        text-align: center;
        min-height: 350px;
        transition: .25s;
    }

    .card-box:hover {
        transform: translateY(-4px);
        box-shadow: 0 14px 35px rgba(0,0,0,0.12);
    }

    .emoji {
        font-size: 85px;
        margin-bottom: 10px;
    }

    .card-title {
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 20px;
        color: #333;
    }

    /* Gradient buttons */
    .stButton>button {
        background: linear-gradient(90deg,#1e62ff,#8a2eff) !important;
        color:white !important;
        padding:14px !important;
        border-radius:14px !important;
        font-size:18px !important;
        font-weight:600 !important;
        width:100% !important;
    }

    </style>
    """, unsafe_allow_html=True)

    # -------------------- LARGE TOP BANNER --------------------
    st.markdown(
        f"""
        <div class="top-banner">
            <div class="banner-title">ZODOPT MEETEASE</div>
            <img src="data:image/png;base64,{logo_b64}" style="height:80px;">
        </div>
        """,
        unsafe_allow_html=True
    )

    # -------------------- MAIN WHITE CONTENT AREA --------------------
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Admin Access</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    # Visit Plan Card
    with col1:
        st.markdown("""
        <div class="card-box">
            <div class="emoji">📅</div>
            <div class="card-title">Visit Plan</div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Open Visit Plan", key="visit_btn", on_click=lambda: navigate_to("visit"))

    # Conference Card
    with col2:
        st.markdown("""
        <div class="card-box">
            <div class="emoji">📘</div>
            <div class="card-title">Conference Booking</div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Open Conference Booking", key="conf_btn", on_click=lambda: navigate_to("conference"))

    st.markdown('</div>', unsafe_allow_html=True)  # End content wrapper

# Run app
load_page()
