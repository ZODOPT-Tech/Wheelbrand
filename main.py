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
        "home":      None,
        "visit":     ("visitor", "visitor_main"),
        "conference":("conference_page", "conference_main"),
    }

    page = st.session_state.current_page

    if page == "home":
        render_home()
        return

    module_name, fn_name = routes.get(page, (None, None))
    if not module_name:
        st.error("Invalid Route")
        return

    module = importlib.import_module(module_name)
    page_fn = getattr(module, fn_name)
    page_fn(navigate_to)

# -------------------- HOME PAGE --------------------
def render_home():

    # Load Logo
    logo = Image.open("zodopt.png")
    buf = io.BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    # CSS
    st.markdown("""
    <style>
    .header {
        width: 100%;
        padding: 25px 40px;
        border-radius: 25px;
        background: linear-gradient(90deg,#1e62ff,#8a2eff);
        color:white;
        display:flex;justify-content:space-between;align-items:center;
        margin-bottom:30px;
    }
    .header-title { font-size: 34px; font-weight:bold; }

    .card {
        background:white;
        padding:50px;
        border-radius:25px;
        width:100%;
        height:100%;
        box-shadow:0 8px 20px rgba(0,0,0,0.08);
        cursor:pointer;
        transition:0.2s;
        text-align:center;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow:0 15px 28px rgba(0,0,0,0.15);
    }

    .icon-circle {
        width:130px;height:130px;border-radius:50%;
        display:flex;justify-content:center;align-items:center;
        margin:auto;
        font-size:55px;color:white;
    }
    .violet { background: linear-gradient(135deg,#4d7cff,#b312ff); }
    .green { background:#00a884; }

    .title { font-size:26px;font-weight:700;margin-top:20px; }
    .btn-bottom {
        margin-top:25px;
        padding:14px;
        width:80%;
        font-size:18px;
        border:none;
        border-radius:12px;
        background:#f0f0f0;
        font-weight:600;
    }
    </style>
    """, unsafe_allow_html=True)

    # HEADER
    st.markdown(
        f"""
        <div class="header">
            <div class="header-title">ZODOPT MEETEASE</div>
            <img src="data:image/png;base64,{logo_b64}" style="height:70px;">
        </div>
        """,
        unsafe_allow_html=True
    )

    # CARDS
    col1, col2 = st.columns([1, 1], gap="large")

    # Visit Plan card
    with col1:
        st.markdown("""
        <div class="card">
            <div class="icon-circle violet">🗓️</div>
            <div class="title">Visit Plan</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Visit Plan", use_container_width=True):
            navigate_to("visit")

    # Conference card
    with col2:
        st.markdown("""
        <div class="card">
            <div class="icon-circle green">📅</div>
            <div class="title">Conference Booking</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Conference Booking", use_container_width=True):
            navigate_to("conference")


# RUN
load_page()
