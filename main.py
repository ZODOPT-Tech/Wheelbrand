# main.py
import streamlit as st
import importlib
from PIL import Image
import base64
from io import BytesIO

# -------------------- Session Init --------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

# -------------------- Navigation --------------------
def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()

# -------------------- Page Loader --------------------
def load_page():
    routes = {
        "home":        None,
        "visit":       ("visitor", "app"),
        "conference":  ("conference_page", "app"),
    }

    page = st.session_state.current_page

    if page == "home":
        return render_home()

    module_name, fn_name = routes.get(page)
    module = importlib.import_module(module_name)
    fn = getattr(module, fn_name)
    fn(navigate_to)

# -----------------------------------------------------
#                      HOME PAGE
# -----------------------------------------------------
def render_home():

    # ---------- LOAD LOGO ----------
    logo = Image.open("zodopt.png")
    buf = BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    # ---------- STYLES ----------
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
        margin-bottom: 30px;
    }
    .header-title { font-size: 34px; font-weight: 700; }

    .card {
        background: white;
        padding: 60px;
        border-radius: 25px;
        box-shadow: 0px 8px 20px rgba(0,0,0,0.08);
        text-align: center;
        cursor: pointer;
        transition: 0.25s;
    }
    .card:hover {
        transform: translateY(-6px);
        box-shadow: 0px 15px 28px rgba(0,0,0,0.18);
    }
    .icon-circle {
        width: 140px;
        height: 140px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 20px auto;
        font-size: 50px;
        color: white;
    }
    .violet { background: linear-gradient(135deg,#4d7cff,#b312ff); }
    .green { background: #00a884; }
    .title-text { font-size: 28px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

    # ---------- HEADER ----------
    st.markdown(
        f"""
        <div class="header">
            <div class="header-title">ZODOPT MEETEASE</div>
            <img src="data:image/png;base64,{logo_b64}" style="height:70px;">
        </div>
        """, unsafe_allow_html=True
    )

    # ---------- FOOTER SPACE ----------
    col1, col2 = st.columns(2, gap="large")

    # ---------- VISIT CARD ----------
    with col1:
        if st.button("", key="visit_btn"):
            navigate_to("visit")

        st.markdown("""
        <div class="card" onclick="window.location.href='/?page_trigger=visit'">
            <div class="icon-circle violet">📅</div>
            <div class="title-text">Visitplan</div>
        </div>
        """, unsafe_allow_html=True)

    # ---------- CONFERENCE CARD ----------
    with col2:
        if st.button("", key="conf_btn"):
            navigate_to("conference")

        st.markdown("""
        <div class="card" onclick="window.location.href='/?page_trigger=conference'">
            <div class="icon-circle green">📘</div>
            <div class="title-text">Conference Booking</div>
        </div>
        """, unsafe_allow_html=True)

    # Detect JS click events
    qp = st.query_params
    if "page_trigger" in qp:
        if qp["page_trigger"] == "visit":
            navigate_to("visit")
        elif qp["page_trigger"] == "conference":
            navigate_to("conference")


# -------------------- RUN APP --------------------
load_page()
