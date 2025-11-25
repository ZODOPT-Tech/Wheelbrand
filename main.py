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
        "home":      {"module": None,                   "fn": None},
        "visit":     {"module": "visitor",              "fn": "visitor_main"},
        "conference":{"module": "conference_page",      "fn": "conference_main"},
    }

    page = st.session_state.current_page

    # Home page is inside this file
    if page == "home":
        return render_home()

    # Load dynamic pages:
    info = routes.get(page)
    if not info:
        st.error("Invalid Page Route")
        return

    module = importlib.import_module(info["module"])
    fn = getattr(module, info["fn"])
    fn(navigate_to)     # Pass navigate_to so the page can navigate back

# ==================================================================
#                           HOME PAGE UI
# ==================================================================
def render_home():

    # Load Logo
    from PIL import Image
    import base64, io

    logo = Image.open("zodopt.png")
    buf = io.BytesIO()
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
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 30px;
    }
    .header-title { font-size: 34px; font-weight: bold; }

    .card {
        background: white;
        padding: 60px;
        border-radius: 25px;
        box-shadow: 0px 8px 20px rgba(0,0,0,0.08);
        text-align: center;
        cursor: pointer;
        transition: 0.2s;
    }
    .card:hover {
        transform: translateY(-6px);
        box-shadow: 0px 15px 28px rgba(0,0,0,0.15);
    }
    .icon-circle {
        width: 140px; height: 140px; border-radius: 50%;
        display: flex; justify-content: center; align-items: center;
        margin: auto;
        font-size: 60px;
        color: white;
    }
    .violet { background: linear-gradient(135deg,#4d7cff,#b312ff); }
    .green  { background: #00a884; }
    .title-text { font-size: 28px; font-weight: 700; margin-top: 20px; }
    .line { width: 70px; height: 7px; border-radius: 4px; margin: 14px auto 0 auto; }
    .violet-line { background:#b312ff; }
    .green-line  { background:#00a884; }
    </style>
    """, unsafe_allow_html=True)

    # ---------- HEADER ----------
    st.markdown(
        f"""
        <div class="header">
            <div class="header-title">ZODOPT MEETEASE</div>
            <img src="data:image/png;base64,{logo_b64}" style="height:70px;">
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------- BIG CLICKABLE CARDS ----------
    col1, col2 = st.columns(2, gap="large")

    with col1:
        if st.container().markdown("""
            <div class="card" onclick="window.location.href='?page=visit'">
                <div class="icon-circle violet">📅</div>
                <div class="title-text">Visitplan</div>
                <div class="line violet-line"></div>
            </div>
        """, unsafe_allow_html=True):
            pass

    with col2:
        if st.container().markdown("""
            <div class="card" onclick="window.location.href='?page=conference'">
                <div class="icon-circle green">📘</div>
                <div class="title-text">Conference Booking</div>
                <div class="line green-line"></div>
            </div>
        """, unsafe_allow_html=True):
            pass

# -------------------- Run App --------------------
load_page()
