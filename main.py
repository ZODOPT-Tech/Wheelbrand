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

    if page not in routes:
        st.error("Invalid Route")
        return

    module_name, function_name = routes[page]

    try:
        module = importlib.import_module(module_name)
        page_fn = getattr(module, function_name)
        page_fn(navigate_to)

    except ModuleNotFoundError:
        st.error(f"Module '{module_name}' not found.")
    except AttributeError:
        st.error(f"Function '{function_name}' missing in module '{module_name}'.")
    except Exception as e:
        st.error(f"Error loading page: {e}")

# -------------------- HOME PAGE --------------------
def render_home():

    # Load Logo
    logo = Image.open("zodopt.png")
    buf = io.BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    # ---------- GLOBAL CSS (Full screen + Buttons) ----------
    st.markdown("""
    <style>
    /* Full screen layout */
    .main, .block-container {
        padding-left: 0 !important;
        padding-right: 0 !important;
        padding-top: 0 !important;
        max-width: 100% !important;
    }

    /* Header */
    .header {
        width: 100%;
        padding: 25px 40px;
        border-radius: 0px;
        background: linear-gradient(90deg,#1e62ff,#8a2eff);
        color:white;
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin-bottom:30px;
    }
    .header-title { font-size: 34px; font-weight:bold; }

    /* Cards */
    .card {
        background:white;
        padding:50px;
        border-radius:25px;
        width:100%;
        height:100%;
        box-shadow:0 8px 20px rgba(0,0,0,0.08);
        text-align:center;
        transition:0.2s;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow:0 18px 35px rgba(0,0,0,0.15);
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

    /* Colored Buttons */
    .stButton>button {
        background: linear-gradient(90deg,#1e62ff,#8a2eff) !important;
        color:white !important;
        padding:14px !important;
        border-radius:12px !important;
        font-size:18px !important;
        font-weight:600 !important;
        width:100% !important;
    }
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

    # ---------- CARDS ----------
    col1, col2 = st.columns([1, 1], gap="large")

    # Visit Plan Card
    with col1:
        st.markdown("""
        <div class="card">
            <div class="icon-circle violet">🗓️</div>
            <div class="title">Visit Plan</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Open Visit Plan", key="visit_btn"):
            navigate_to("visit")

    # Conference Card
    with col2:
        st.markdown("""
        <div class="card">
            <div class="icon-circle green">📅</div>
            <div class="title">Conference Booking</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Open Conference Booking", key="conf_btn"):
            navigate_to("conference")


# RUN
load_page()

