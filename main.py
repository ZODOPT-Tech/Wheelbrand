import streamlit as st
import importlib
from PIL import Image
import base64
from io import BytesIO

# ---------------- SESSION SETUP ----------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"


def navigate_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()


# ---------------- PAGE LOADER ----------------
def load_page():
    routes = {
        "home": {"module": None, "fn": None},
        "visit": {"module": "visitor", "fn": "render_visitor_page"},
        "conference": {"module": "conference_page", "fn": "render_conference_page"},
    }

    page = st.session_state.current_page

    if page == "home":
        return render_home()

    info = routes.get(page)
    if not info:
        st.error("Invalid route")
        return

    module = importlib.import_module(info["module"])
    fn = getattr(module, info["fn"])
    fn(navigate_to)


# =====================================================================
#                             HOME PAGE
# =====================================================================
def render_home():

    # -------- LOAD LOGO --------
    logo = Image.open("zodopt.png")
    buf = BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    # --------- CSS ---------
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
        margin-bottom: 35px;
    }
    .header-title { font-size: 34px; font-weight: 700; }
    .logo-img { height: 70px; }

    .card {
        background: white;
        padding: 70px;
        border-radius: 28px;
        box-shadow: 0px 10px 25px rgba(0,0,0,0.15);
        text-align: center;
        cursor: pointer;
        transition: 0.2s ease-in-out;
        width: 100%;
    }
    .card:hover {
        transform: translateY(-6px);
    }

    .icon-circle {
        width: 150px; height: 150px;
        border-radius: 50%;
        display: flex; justify-content: center; align-items: center;
        margin: 0 auto 20px auto;
        font-size: 70px; color: white;
    }
    .violet { background: linear-gradient(135deg,#4d7cff,#b312ff); }
    .green { background: #00a884; }

    .title-btn {
        margin-top: 20px;
        background: none;
        border: none;
        font-size: 30px;
        font-weight: 700;
        color: #222;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)

    # -------- HEADER --------
    st.markdown(
        f"""
        <div class="header">
            <div class="header-title">ZODOPT MEETEASE</div>
            <img class="logo-img" src="data:image/png;base64,{logo_b64}">
        </div>
        """,
        unsafe_allow_html=True
    )

    # -------- TWO WIDE CARDS --------
    col1, col2 = st.columns([1, 1], gap="large")

    # ========== VISIT PLAN CARD ==========
    with col1:
        card = st.container()
        with card:
            st.markdown(
                """
                <div class="card">
                    <div class="icon-circle violet">🗓️</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # BUTTON inside card
            if st.button("Visit Plan", key="visit_plan_btn", use_container_width=True):
                navigate_to("visit")

        # Make entire card clickable too
        if card:
            st.markdown(
                "<script>document.querySelectorAll('.card')[0].onclick=function(){window.location.href='?page=visit'};</script>",
                unsafe_allow_html=True,
            )

    # ========== CONFERENCE CARD ==========
    with col2:
        card2 = st.container()
        with card2:
            st.markdown(
                """
                <div class="card">
                    <div class="icon-circle green">📅</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button("Conference Booking", key="conf_btn", use_container_width=True):
                navigate_to("conference")

        if card2:
            st.markdown(
                "<script>document.querySelectorAll('.card')[1].onclick=function(){window.location.href='?page=conference'};</script>",
                unsafe_allow_html=True,
            )


# ---------------- RUN ----------------
load_page()
