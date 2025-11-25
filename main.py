import streamlit as st
import importlib
from PIL import Image
import base64
from io import BytesIO

# -------------------- SESSION NAVIGATION --------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

def navigate_to(page):
    st.session_state.current_page = page
    st.rerun()

# -------------------- PAGE LOADER --------------------
def load_page():
    routes = {
        "home": {"module": None, "function": None},
        "visit": {"module": "visitor", "function": "visitor_main"},
        "conference": {"module": "conference_page", "function": "conference_main"},
    }

    page = st.session_state.current_page

    # HOME PAGE IS INSIDE THIS FILE
    if page == "home":
        return render_home(navigate_to)

    # IMPORT OTHER PAGES
    module_name = routes[page]["module"]
    fn_name = routes[page]["function"]

    module = importlib.import_module(module_name)
    fn = getattr(module, fn_name)
    fn(navigate_to)

# ==================================================================
#                         HOME UI
# ==================================================================
def render_home(navigate_to):
    st.set_page_config(page_title="ZODOPT MEETEASE", layout="wide")

    # Load logo
    logo = Image.open("zodopt.png")
    buf = BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    # -------------------- CSS --------------------
    st.markdown("""
    <style>
    .header {
        width: 100%;
        padding: 30px 45px;
        border-radius: 22px;
        background: linear-gradient(90deg,#1e62ff,#8a2eff);
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 40px;
    }
    .header-title {
        font-size: 40px;
        font-weight: 800;
    }
    .logo-img {
        height: 85px;
    }

    .card {
        background: white;
        padding: 80px;
        border-radius: 28px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        text-align: center;
        width: 100%;
        cursor: pointer;
        transition: 0.25s;
    }

    .card:hover {
        transform: scale(1.04);
        box-shadow: 0px 20px 40px rgba(0,0,0,0.18);
    }

    .icon-circle {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 70px;
        color: white;
        margin: 0 auto 25px auto;
    }

    .violet { background: linear-gradient(135deg,#4d7cff,#b312ff); }
    .green { background: #00a884; }

    .title-text {
        font-size: 32px;
        font-weight: 700;
        margin-top: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

    # -------------------- HEADER --------------------
    st.markdown(
        f"""
        <div class="header">
            <div class="header-title">ZODOPT MEETEASE</div>
            <img src="data:image/png;base64,{logo_b64}" class="logo-img">
        </div>
        """,
        unsafe_allow_html=True
    )

    # -------------------- FULL WIDTH CARDS --------------------
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        if st.markdown(
            """
            <div class="card" onclick="window.location.href='?page=visit'">
                <div class="icon-circle violet">🗓️</div>
                <div class="title-text">Visit Plan</div>
            </div>
            """,
            unsafe_allow_html=True
        ):
            pass

    with col2:
        if st.markdown(
            """
            <div class="card" onclick="window.location.href='?page=conference'">
                <div class="icon-circle green">📅</div>
                <div class="title-text">Conference Booking</div>
            </div>
            """,
            unsafe_allow_html=True
        ):
            pass

# Run application
load_page()
