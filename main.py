# main.py
import streamlit as st
import importlib
from PIL import Image
import base64
from io import BytesIO

# -------------------- Session --------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"


def navigate_to(page):
    st.session_state.current_page = page
    st.rerun()


# -------------------- Loader --------------------
def load_page():
    pages = {
        "home": None,
        "visit": ("visitor", "render_visitor_page"),
        "conference": ("conference_page", "render_conference_page")
    }

    current = st.session_state.current_page

    if current == "home":
        render_home()
        return

    module_name, fn_name = pages[current]
    module = importlib.import_module(module_name)
    fn = getattr(module, fn_name)
    fn(navigate_to)


# ==============================
#         HOME PAGE UI
# ==============================
def render_home():

    # Load logo
    logo = Image.open("zodopt.png")
    buf = BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    st.set_page_config(layout="wide")

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
        font-size: 34px;
        font-weight: 700;
    }

    .card {
        background: white;
        padding: 70px;
        border-radius: 30px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.10);
        text-align: center;
        transition: 0.2s;
        cursor: pointer;
        width: 100%;
    }
    .card:hover {
        transform: translateY(-6px);
        box-shadow: 0px 18px 35px rgba(0,0,0,0.15);
    }

    .icon-circle {
        width: 170px; height: 170px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 70px;
        color: white;
        margin: auto;
    }
    .violet { background: linear-gradient(135deg,#4d7cff,#b312ff); }
    .green { background: #00a884; }

    .title-text {
        font-size: 34px;
        font-weight: 700;
        margin-top: 25px;
    }

    /* Make the entire block clickable */
    .clickable {
        text-decoration: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # -------- Header --------
    st.markdown(
        f"""
        <div class="header">
            <div class="header-title">ZODOPT MEETEASE</div>
            <img src="data:image/png;base64,{logo_b64}" height="70">
        </div>
        """,
        unsafe_allow_html=True
    )

    # -------- Wide Cards --------
    col1, col2 = st.columns([1, 1], gap="large")  # wide & equal spacing

    with col1:
        clicked = st.container().markdown(
            """
            <a href="?page=visit" class="clickable">
                <div class="card">
                    <div class="icon-circle violet">📅</div>
                    <div class="title-text">Visit Plan</div>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )

    with col2:
        clicked = st.container().markdown(
            """
            <a href="?page=conference" class="clickable">
                <div class="card">
                    <div class="icon-circle green">📗</div>
                    <div class="title-text">Conference Booking</div>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )


# -------------------- RUN --------------------
load_page()
