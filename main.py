import streamlit as st
from PIL import Image
import base64
from io import BytesIO
import importlib

st.set_page_config(page_title="ZODOPT MEETEASE", layout="wide")

# -------------------- SESSION NAVIGATION --------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"   # default

def navigate(page_name):
    st.session_state.current_page = page_name
    st.rerun()

# -------------------- PAGE LOADER --------------------
def load_page():
    page = st.session_state.current_page

    if page == "visitor":
        visitor = importlib.import_module("visitor")
        visitor.render()          # visitor.py must have render()
        return

    elif page == "conference":
        conference = importlib.import_module("conference_page")
        conference.render()       # conference_page.py must have render()
        return

    # Otherwise show HOME (cards)
    show_home()


# -------------------- HOME SCREEN (CARDS ONLY) --------------------
def show_home():

    # -------- LOGO --------
    logo = Image.open("zodopt.png")
    buf = BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    # -------- STYLES --------
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
    }
    .header-title { font-size: 34px; font-weight: 700; }
    .logo-img { height: 70px; }

    .card {
        background-color: white;
        padding: 60px;
        border-radius: 25px;
        box-shadow: 0px 8px 20px rgba(0,0,0,0.08);
        text-align: center;
        width: 100%;
        cursor: pointer;
        transition: 0.2s ease-in-out;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0px 12px 25px rgba(0,0,0,0.12);
    }
    .icon-circle {
        width: 120px; height: 120px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 25px auto;
        font-size: 45px; color: white;
    }
    .violet { background: linear-gradient(135deg,#4d7cff,#b312ff); }
    .green { background: #00a884; }
    .title-text { font-size: 28px; font-weight: 600; }
    .line { width: 70px; height: 7px; border-radius: 4px; margin: 14px auto 0 auto; }
    .violet-line { background:#b312ff; }
    .green-line { background:#00a884; }
    </style>
    """, unsafe_allow_html=True)

    # -------- HEADER --------
    st.markdown(
        f"""
        <div class="header">
            <div class="header-title">ZODOPT MEETEASE</div>
            <img src="data:image/png;base64,{logo_b64}" class="logo-img">
        </div>
        """, unsafe_allow_html=True
    )

    st.write("")

    # -------- BUTTON CARDS --------
    col1, col2 = st.columns(2, gap="large")

    with col1:
        if st.markdown(
            """
            <div class="card" onclick="window.location.href='?page=visitor'">
                <div class="icon-circle violet">📅</div>
                <div class="title-text">Visitplan</div>
                <div class="line violet-line"></div>
            </div>
            """,
            unsafe_allow_html=True
        ):
            pass

        if st.button("Open Visitplan", key="visit_hidden", help="Click the card above"):
            navigate("visitor")

    with col2:
        if st.markdown(
            """
            <div class="card" onclick="window.location.href='?page=conference'">
                <div class="icon-circle green">📆</div>
                <div class="title-text">Conference Booking</div>
                <div class="line green-line"></div>
            </div>
            """,
            unsafe_allow_html=True
        ):
            pass

        if st.button("Open Conference", key="conf_hidden", help="Click the card above"):
            navigate("conference")


# -------------------- RUN --------------------
load_page()
