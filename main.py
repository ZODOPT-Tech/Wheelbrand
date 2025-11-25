# main.py
import streamlit as st
import importlib

# -------------------- Init Session --------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

# -------------------- Navigation Function --------------------
def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()

# -------------------- Page Loader --------------------
def load_page():

    routes = {
        "home":        {"module": None,                   "fn": None},
        "visit":       {"module": "visitor",              "fn": "visitor_main"},
        "conference":  {"module": "conference_page",      "fn": "conference_main"},
    }

    page = st.session_state.current_page

    # Home page is inside this file
    if page == "home":
        return render_home()

    # Dynamic page load
    info = routes.get(page)

    if info is None:
        st.error("❌ Invalid Route")
        return

    module = importlib.import_module(info["module"])
    fn = getattr(module, info["fn"])

    fn(navigate_to)     # Call page entrypoint

# ==================================================================
#                       HOME PAGE UI
# ==================================================================
def render_home():
    from PIL import Image
    import base64, io

    st.set_page_config(page_title="ZODOPT MEETEASE", layout="wide")

    # Load logo
    logo = Image.open("zodopt.png")
    buf = io.BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    # ---------------- STYLES ----------------
    st.markdown("""
    <style>
    .header {
        width: 100%;
        padding: 28px 40px;
        border-radius: 25px;
        background: linear-gradient(90deg,#1e62ff,#8a2eff);
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 40px;
    }
    .header-title { font-size: 36px; font-weight: 800; }

    .card {
        background: white;
        padding: 70px;
        border-radius: 30px;
        box-shadow: 0px 8px 22px rgba(0,0,0,0.08);
        text-align: center;
        cursor: pointer;
        transition: 0.18s;
        width: 100%;
    }
    .card:hover {
        transform: scale(1.03);
        box-shadow: 0px 15px 28px rgba(0,0,0,0.18);
    }

    .icon-circle {
        width: 150px; height: 150px; border-radius: 50%;
        display: flex; justify-content: center; align-items: center;
        margin: auto;
        font-size: 70px;
        color: white;
    }
    .violet { background: linear-gradient(135deg,#4d7cff,#b312ff); }
    .green  { background: #00a884; }

    .title-text {
        font-size: 30px; 
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
            <img src="data:image/png;base64,{logo_b64}" style="height:75px;">
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------- CARDS ----------------
    col1, col2 = st.columns([1,1], gap="large")

    with col1:
        if st.markdown("""
            <div class="card" onclick="window.location.href='?page=visit'">
                <div class="icon-circle violet">🗓️</div>
                <div class="title-text">Visit Plan</div>
            </div>
        """, unsafe_allow_html=True):
            pass

    with col2:
        if st.markdown("""
            <div class="card" onclick="window.location.href='?page=conference'">
                <div class="icon-circle green">📅</div>
                <div class="title-text">Conference Booking</div>
            </div>
        """, unsafe_allow_html=True):
            pass

# -------------------- RUN APP --------------------
load_page()
