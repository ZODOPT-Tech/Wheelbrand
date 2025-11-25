import streamlit as st
from PIL import Image
import base64
from io import BytesIO


# MUST BE AT TOP – Not inside any function
st.set_page_config(page_title="ZODOPT MEETEASE", layout="wide")


def render_main_home(navigate_to):

    # -------- Load Logo --------
    logo = Image.open("zodopt.png")
    buf = BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    # -------- CSS --------
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
    .header-title { font-size: 34px; font-weight: 700; }
    .logo-img { height: 70px; }

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
        box-shadow: 0px 14px 28px rgba(0,0,0,0.15);
    }

    .icon-circle {
        width: 130px; height: 130px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 20px auto;
        font-size: 55px; color: white;
    }

    .violet { background: linear-gradient(135deg,#4d7cff,#b312ff); }
    .green  { background: #00a884; }
    .title-text { font-size: 28px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

    # -------- HEADER --------
    st.markdown(
        f"""
        <div class="header">
            <div class="header-title">ZODOPT MEETEASE</div>
            <img src="data:image/png;base64,{logo_b64}" class="logo-img">
        </div>
        """,
        unsafe_allow_html=True
    )

    # -------- TWO BIG CARDS --------
    col1, col2 = st.columns(2, gap="large")

    # ---- VISIT PLAN ----
    with col1:
        clicked = st.container()
        clicked.markdown("""
            <div class="card" id="visit_card">
                <div class="icon-circle violet">🗓️</div>
                <div class="title-text">Visitplan</div>
            </div>
        """, unsafe_allow_html=True)

        # Make card clickable using JS → Run navigate_to()
        st.markdown("""
            <script>
            const card = document.getElementById("visit_card");
            card.addEventListener("click", function() {
                window.parent.postMessage({type: "streamlit:setSessionState", state: {current_page: "visit"}}, "*");
            });
            </script>
        """, unsafe_allow_html=True)

    # ---- CONFERENCE ----
    with col2:
        clicked2 = st.container()
        clicked2.markdown("""
            <div class="card" id="conf_card">
                <div class="icon-circle green">📘</div>
                <div class="title-text">Conference Booking</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <script>
            const card2 = document.getElementById("conf_card");
            card2.addEventListener("click", function() {
                window.parent.postMessage({type: "streamlit:setSessionState", state: {current_page: "conference"}}, "*");
            });
            </script>
        """, unsafe_allow_html=True)
