import streamlit as st
import importlib
from PIL import Image
from io import BytesIO
import base64

# -------------------- Init Session --------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

# -------------------- Navigation Function --------------------
def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()

# ==================================================================
#                          PAGE LOADER
# ==================================================================
def load_page():
    routes = {
        "home": {"module": None, "fn": None},
        "visit": {"module": "visitor", "fn": "render_visitor_page"},
        "conference": {"module": "conference_page", "fn": "render_conference_page"},
    }

    page = st.session_state.current_page

    if page == "home":
        return render_home(navigate_to)

    info = routes.get(page)
    if not info:
        st.error("Invalid Page Route")
        return

    module = importlib.import_module(info["module"])
    fn = getattr(module, info["fn"])
    fn(navigate_to)

# ==================================================================
#                         HOME PAGE UI
# ==================================================================
def render_home(navigate_to):

    st.set_page_config(page_title="ZODOPT MEETEASE", layout="wide")

    # Load logo
    logo = Image.open("zodopt.png")
    buf = BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    # ---------- STYLES ----------
    st.markdown("""
    <style>
    .header {
        width: 100%;
        padding: 30px 45px;
        border-radius: 25px;
        background: linear-gradient(90deg,#1e62ff,#8a2eff);
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 35px;
    }
    .header-title { font-size: 38px; font-weight: bold; }

    .card-button {
        background: white;
        padding: 70px;
        border-radius: 30px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.10);
        text-align: center;
        cursor: pointer;
        width: 100%;
        transition: 0.2s;
    }
    .card-button:hover {
        transform: translateY(-7px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }
    .icon-circle {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        margin: auto;
        font-size: 70px;
        color: white;
    }
    .violet { background: linear-gradient(135deg,#4d7cff,#b312ff); }
    .green  { background: #00a884; }
    .title-text {
        font-size: 32px;
        margin-top: 25px;
        font-weight: 700;
    }
    .click-btn {
        width: 80%;
        margin-top: 25px;
        padding: 14px;
        background: linear-gradient(90deg,#1e62ff,#8a2eff);
        border-radius: 12px;
        color: white;
        font-size: 20px;
        font-weight: 600;
        border: none;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---------- HEADER ----------
    st.markdown(
        f"""
        <div class="header">
            <div class="header-title">ZODOPT MEETEASE</div>
            <img src="data:image/png;base64,{logo_b64}" style="height:80px;">
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------- FULL-WIDTH CARDS ----------
    col1, col2 = st.columns([1,1], gap="large")

    # ---------- VISIT PLAN ----------
    with col1:
        if st.button("VisitPlan_Click", key="visit_click", help="", use_container_width=True):
            navigate_to("visit")

        st.markdown("""
            <div class="card-button" onclick="document.getElementById('visit_click').click()">
                <div class="icon-circle violet">🗓️</div>
                <div class="title-text">Visit Plan</div>
                <button class="click-btn">Open Visit Plan</button>
            </div>
        """, unsafe_allow_html=True)

    # ---------- CONFERENCE ----------
    with col2:
        if st.button("Conf_Click", key="conference_click", help="", use_container_width=True):
            navigate_to("conference")

        st.markdown("""
            <div class="card-button" onclick="document.getElementById('conference_click').click()">
                <div class="icon-circle green">📘</div>
                <div class="title-text">Conference Booking</div>
                <button class="click-btn">Open Conference</button>
            </div>
        """, unsafe_allow_html=True)

# ==================================================================
#                           RUN APP
# ==================================================================
load_page()
