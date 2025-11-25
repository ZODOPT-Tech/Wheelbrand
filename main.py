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
        page_fn = getattr(module, fn_name)
        page_fn(navigate_to)
    except Exception as e:
        st.error(f"Error loading page: {e}")

# -------------------- HOME PAGE --------------------
def render_home():

    # Load Logo
    logo = Image.open("zodopt.png")
    buf = io.BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    # ---------- PROFESSIONAL CSS ----------
    st.markdown("""
    <style>

    /* Limit content width for professional look */
    .block-container {
        max-width: 1050px !important;
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }

    /* Header full width */
    .header {
        width: 100vw;
        margin-left: calc(-50vw + 50%);
        padding: 22px 40px;
        background: linear-gradient(90deg,#1e62ff,#8a2eff);
        color:white;
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin-bottom:40px;
    }

    .header-title {
        font-size: 30px;
        font-weight:800;
    }

    /* Cards */
    .card {
        background:white;
        padding:40px;
        border-radius:20px;
        width:100%;
        min-height:330px;
        box-shadow:0 8px 20px rgba(0,0,0,0.08);
        text-align:center;
        transition:0.2s;
    }

    .card:hover {
        transform: translateY(-4px);
        box-shadow:0 15px 32px rgba(0,0,0,0.12);
    }

    .icon-circle {
        width:115px;height:115px;border-radius:50%;
        display:flex;justify-content:center;align-items:center;
        margin:auto;
        font-size:48px;color:white;
    }

    .violet { background: linear-gradient(135deg,#4d7cff,#b312ff); }
    .green { background:#00a884; }
    
    .title {
        font-size:23px;
        font-weight:700;
        margin-top:20px;
    }

    /* Gradient Buttons */
    .stButton>button {
        background: linear-gradient(90deg,#1e62ff,#8a2eff) !important;
        color:white !important;
        padding:12px !important;
        border-radius:12px !important;
        font-size:17px !important;
        font-weight:600 !important;
    }

    </style>
    """, unsafe_allow_html=True)

    # ---------- HEADER ----------
    st.markdown(
        f"""
        <div class="header">
            <div class="header-title">ZODOPT MEETEASE</div>
            <img src="data:image/png;base64,{logo_b64}" style="height:60px;">
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------- CARDS ----------
    col1, col2 = st.columns(2, gap="large")

    # Visit Plan Card
    with col1:
        st.markdown("""
        <div class="card">
            <div class="icon-circle violet">🗓️</div>
            <div class="title">Visit Plan</div>
        </div>
        """, unsafe_allow_html=True)

        st.button("Open Visit Plan", key="visit", on_click=lambda: navigate_to("visit"))

    # Conference Booking Card
    with col2:
        st.markdown("""
        <div class="card">
            <div class="icon-circle green">📅</div>
            <div class="title">Conference Booking</div>
        </div>
        """, unsafe_allow_html=True)

        st.button("Open Conference Booking", key="conf", on_click=lambda: navigate_to("conference"))


# RUN
load_page()
