# main.py
import streamlit as st
import importlib
from PIL import Image
import base64
from io import BytesIO

# ---------------- SESSION NAVIGATION ----------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()


# ---------------- PAGE LOADER ----------------
def load_page():
    routes = {
        "home": {"module": None, "fn": None},
        "visit": {"module": "visitor", "fn": "visitor_main"},
        "conference": {"module": "conference_page", "fn": "conference_main"},
    }

    current = st.session_state.current_page

    if current == "home":
        render_home()
        return

    info = routes.get(current)
    module = importlib.import_module(info["module"])
    page_fn = getattr(module, info["fn"])
    page_fn(navigate_to)


# ---------------- HOME PAGE UI ----------------
def render_home():

    st.set_page_config(page_title="ZODOPT MEETEASE", layout="wide")

    # Load logo
    logo = Image.open("zodopt.png")
    buf = BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    # ---------------- STYLE ----------------
    st.markdown("""
    <style>
    .header {
        width: 100%;
        padding: 25px 40px;
        border-radius: 25px;
        background: linear-gradient(90deg,#1e62ff,#8a2eff);
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 40px;
    }
    .header-title {
        font-size: 36px;
        font-weight: 800;
    }
    .card {
        background: white;
        padding: 80px 40px;
        border-radius: 30px;
        box-shadow: 0 12px 32px rgba(0,0,0,0.10);
        text-align: center;
        width: 100%;
        cursor: pointer;
        transition: 0.2s;
        border: 3px solid transparent;
    }
    .card:hover {
        transform: translateY(-8px);
        border: 3px solid #8a2eff;
    }
    .icon-circle {
        width: 160px;
        height: 160px;
        border-radius: 50%;
        margin: auto;
        display: flex;
        justify-content: center;
        align-items: center;
        color: white;
        font-size: 70px;
    }
    .violet { background: linear-gradient(135deg,#4d7cff,#b312ff); }
    .green { background: #00a884; }
    .title-text {
        font-size: 34px;
        font-weight: 700;
        margin-top: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---------------- HEADER ----------------
    st.markdown(
        f"""
        <div class="header">
            <div class="header-title">ZODOPT MEETEASE</div>
            <img src="data:image/png;base64,{logo_b64}" style="height:80px;">
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------- WIDE TWO CARDS ----------------
    col1, col2 = st.columns(2, gap="large")

    with col1:
        if st.container().button(" ", key="visit_card_btn", help="Open Visit Plan"):
            navigate_to("visit")

        st.markdown("""
            <div class="card">
                <div class="icon-circle violet">📅</div>
                <div class="title-text">Visit Plan</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        if st.container().button(" ", key="conf_card_btn", help="Open Conference"):
            navigate_to("conference")

        st.markdown("""
            <div class="card">
                <div class="icon-circle green">📘</div>
                <div class="title-text">Conference Booking</div>
            </div>
        """, unsafe_allow_html=True)


# ---------------- RUN APP ----------------
load_page()
