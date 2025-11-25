import streamlit as st
from PIL import Image
import base64
from io import BytesIO

def render_main_home(navigate_to):

    st.set_page_config(page_title="ZODOPT MEETEASE", layout="wide")

    # Load Logo
    logo = Image.open("zodopt.png")
    buf = BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    # ---------- CSS ----------
    st.markdown("""
    <style>
    .header {
        width: 100%;
        padding: 25px 40px;
        border-radius: 25px;
        background: linear-gradient(90deg,#1e62ff,#8a2eff);
        color: white;
        display: flex; justify-content: space-between; align-items: center;
    }
    .header-title { font-size: 34px; font-weight: 700; }
    .logo-img { height: 70px; }

    .card {
        background: white; padding: 60px;
        border-radius: 25px;
        box-shadow: 0px 8px 20px rgba(0,0,0,0.08);
        text-align: center;
        cursor: pointer;
        transition: 0.18s;
    }
    .card:hover { transform: translateY(-6px); box-shadow: 0px 15px 30px rgba(0,0,0,0.18); }

    .icon-circle {
        width: 130px; height: 130px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 55px; margin: auto; color: white;
    }
    .violet { background: linear-gradient(135deg,#4d7cff,#b312ff); }
    .green { background: #00a884; }

    .title-text {
        font-size: 28px; font-weight: 700; margin-top: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---------- HEADER ----------
    st.markdown(
        f"""
        <div class="header">
            <div class="header-title">ZODOPT MEETEASE</div>
            <img src="data:image/png;base64,{logo_b64}" class="logo-img">
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------- Cards ----------
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            f"""
            <div class="card" onclick="window.location.href='?page=visit'">
                <div class="icon-circle violet">🗓️</div>
                <div class="title-text">Visit Plan</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="card" onclick="window.location.href='?page=conference'">
                <div class="icon-circle green">📅</div>
                <div class="title-text">Conference Booking</div>
            </div>
            """,
            unsafe_allow_html=True
        )


# ---------- RUN FOR TESTING DIRECTLY ----------
if __name__ == "__main__":
    render_main_home(lambda x: None)
