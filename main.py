import streamlit as st
from PIL import Image
import base64
from io import BytesIO

st.set_page_config(page_title="ZODOPT MEETEASE", layout="wide")

def navigate_to(page):
    st.session_state["current_page"] = page
    st.rerun()

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "home"

# ---------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------
if st.session_state["current_page"] == "home":

    # Load logo
    logo = Image.open("zodopt.png")
    buf = BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    # Styles
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
        background: white; padding: 70px;
        border-radius: 30px; width: 100%;
        box-shadow: 0px 10px 25px rgba(0,0,0,0.10);
        text-align: center; cursor: pointer;
        transition: 0.25s ease;
    }
    .card:hover {
        transform: translateY(-6px);
        box-shadow: 0px 18px 35px rgba(0,0,0,0.15);
    }
    .icon-circle {
        width: 140px; height: 140px; border-radius: 50%;
        display: flex; justify-content: center; align-items: center;
        margin: auto;
        font-size: 60px; color: white;
    }
    .violet { background: linear-gradient(135deg,#4d7cff,#b312ff); }
    .green { background: #00a884; }

    .title-text { font-size: 30px; font-weight: 700; margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown(
        f"""
        <div class="header">
            <div class="header-title">ZODOPT MEETEASE</div>
            <img src="data:image/png;base64,{logo_b64}" class="logo-img">
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    # -------------------- FIXED CLICKABLE CARDS --------------------
    col1, col2 = st.columns(2, gap="large")

    # Visit Plan
    with col1:
        btn = st.button(" ", key="visit_btn", help="Visit Plan", use_container_width=True)
        if btn:
            navigate_to("visit")

        st.markdown("""
            <div class="card">
                <div class="icon-circle violet">🗓️</div>
                <div class="title-text">Visit Plan</div>
            </div>
        """, unsafe_allow_html=True)

    # Conference Booking
    with col2:
        btn2 = st.button(" ", key="conf_btn", help="Conference Booking", use_container_width=True)
        if btn2:
            navigate_to("conference")

        st.markdown("""
            <div class="card">
                <div class="icon-circle green">📅</div>
                <div class="title-text">Conference Booking</div>
            </div>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------
# PAGE ROUTING
# ---------------------------------------------------------

elif st.session_state["current_page"] == "visit":
    import visitor
    visitor.visitor_main(navigate_to)

elif st.session_state["current_page"] == "conference":
    import conference_page
    conference_page.conference_main(navigate_to)
