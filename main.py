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

# -------------------- HOME PAGE --------------------
def render_home():

    # Load Logo
    logo = Image.open("zodopt.png")
    buf = io.BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    # -------------------- CSS --------------------
    st.markdown("""
    <style>

    /* Full-width container */
    .block-container {
        max-width: 100% !important;
        padding-top: 0rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* Header full width */
    .header {
        width: 100vw;
        margin-left: calc(-50vw + 50%);
        padding: 20px 40px;
        background: linear-gradient(90deg,#1e62ff,#8a2eff);
        color:white;
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin-bottom:40px;
    }
    .header-title { font-size: 30px; font-weight:800; }

    /* CARD (45% width look) */
    .clean-card {
        background:white;
        padding:60px 20px;
        border-radius:32px;
        text-align:center;
        box-shadow:0px 12px 35px rgba(0,0,0,0.08);
        width:100%;
        min-height:380px;
        transition:0.2s;
    }

    .clean-card:hover {
        transform: translateY(-4px);
        box-shadow:0px 18px 45px rgba(0,0,0,0.12);
    }

    .icon-emoji {
        font-size:95px;
        display:block;
        margin-bottom:20px;
    }

    .title {
        font-size:26px;
        font-weight:700;
        margin-bottom:30px;
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

    # ---------------- HEADER ----------------
    st.markdown(
        f"""
        <div class="header">
            <div class="header-title">ZODOPT MEETEASE</div>
            <img src="data:image/png;base64,{logo_b64}" style="height:58px;">
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------- 45% + 45% CARDS ----------------
    col1, col2 = st.columns([1, 1], gap="large")

    # Visit Plan
    with col1:
        st.markdown("""
        <div class="clean-card">
            <div class="icon-emoji">📅</div>
            <div class="title">Visit Plan</div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Open Visit Plan", key="visit", on_click=lambda: navigate_to("visit"))

    # Conference Booking
    with col2:
        st.markdown("""
        <div class="clean-card">
            <div class="icon-emoji">📘</div>
            <div class="title">Conference Booking</div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Open Conference Booking", key="conference", on_click=lambda: navigate_to("conference"))


# Run App
load_page()
