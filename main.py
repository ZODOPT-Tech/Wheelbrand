import streamlit as st
import importlib
from PIL import Image
import base64
from io import BytesIO

st.set_page_config(page_title="ZODOPT MEETEASE", layout="wide")

# ---------------------- INIT SESSION ----------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

def navigate_to(page):
    st.session_state.current_page = page
    st.rerun()

# ---------------------- HEADER ----------------------
logo = Image.open("zodopt.png")
buf = BytesIO()
logo.save(buf, format="PNG")
logo_b64 = base64.b64encode(buf.getvalue()).decode()

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
}
.card:hover {
    transform: translateY(-5px);
    box-shadow: 0px 12px 25px rgba(0,0,0,0.12);
}
</style>
""", unsafe_allow_html=True)

def show_header():
    st.markdown(f"""
    <div class="header">
        <div class="header-title">ZODOPT MEETEASE</div>
        <img src="data:image/png;base64,{logo_b64}" class="logo-img">
    </div>
    """, unsafe_allow_html=True)

# ---------------------- HOME UI ----------------------
def show_home_page():
    show_header()
    st.write("")
    
    col1, col2 = st.columns(2, gap="large")

    with col1:
        if st.button("Visit Plan", use_container_width=True):
            navigate_to("visitor")
        st.markdown("""
        <div class="card">
            <div style="font-size:50px;">🗓️</div>
            <h3>Visitplan</h3>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if st.button("Conference", use_container_width=True):
            navigate_to("conference")
        st.markdown("""
        <div class="card">
            <div style="font-size:50px;">📅</div>
            <h3>Conference Booking</h3>
        </div>
        """, unsafe_allow_html=True)

# ---------------------- PAGE LOADER ----------------------
def load_page():
    page = st.session_state.current_page

    if page == "home":
        show_home_page()

    elif page == "visitor":
        module = importlib.import_module("visitor")
        module.render(navigate_to)   # call visitor.py render()

    elif page == "conference":
        module = importlib.import_module("conference_page")
        module.render(navigate_to)   # call conference_page.py render()

    else:
        st.error("Page not found")

# ---------------------- RUN ----------------------
load_page()
