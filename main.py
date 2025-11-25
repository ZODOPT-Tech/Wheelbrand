import streamlit as st
from PIL import Image
import base64
from io import BytesIO
import importlib

st.set_page_config(page_title="ZODOPT MEETEASE", layout="wide")

# ---------------- PAGE ROUTING ----------------
query_params = st.query_params

if "page" in query_params:
    page = query_params["page"]

    if page == "visit":
        visitor = importlib.import_module("visitor")
        if hasattr(visitor, "app"):
            visitor.app()
        else:
            st.write("Loading visitor page...")
            st.experimental_rerun()
        st.stop()

    elif page == "conference":
        conf = importlib.import_module("conference")
        if hasattr(conf, "app"):
            conf.app()
        else:
            st.write("Loading conference page...")
            st.experimental_rerun()
        st.stop()

# ---------------- DEFAULT MAIN SCREEN ----------------

logo = Image.open("zodopt.png")
buffer = BytesIO()
logo.save(buffer, format="PNG")
logo_base64 = base64.b64encode(buffer.getvalue()).decode()

# ---------------- HEADER STYLE ----------------
st.markdown("""
<style>
.header {
    width: 100%;
    padding: 25px 40px;
    border-radius: 25px;
    background: linear-gradient(90deg, #1e62ff, #8a2eff);
    color: white;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.header-title {
    font-size: 34px;
    font-weight: 700;
}
.logo-img { height: 70px; }

.card {
    background-color: white;
    padding: 60px;
    border-radius: 25px;
    box-shadow: 0px 8px 20px rgba(0,0,0,0.08);
    text-align: center;
    width: 100%;
    transition: .2s;
    cursor: pointer;
    display: block;
    text-decoration: none !important;
}
.card:hover {
    transform: translateY(-5px);
    box-shadow: 0px 12px 25px rgba(0,0,0,0.12);
}
.icon-circle {
    width: 110px;
    height: 110px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 20px auto;
    font-size: 40px;
    color: white;
}
.violet { background: linear-gradient(135deg, #4d7cff, #b312ff); }
.green  { background: #00a884; }

.title-text {
    font-size: 24px;
    font-weight: 600;
    margin-top: 10px;
}
.line {
    width: 60px;
    height: 6px;
    border-radius: 4px;
    margin: 12px auto 0 auto;
}
.violet-line { background: #b312ff; }
.green-line  { background: #00a884; }

a { text-decoration: none; }
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown(
    f"""
    <div class="header">
        <div class="header-title">ZODOPT MEETEASE</div>
        <img src="data:image/png;base64,{logo_base64}" class="logo-img">
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

# ---------------- BUTTONS ----------------
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown(
        """
        <a class="card" href="?page=visit" target="_self">
            <div class="icon-circle violet">🗓️</div>
            <div class="title-text">Visitplan</div>
            <div class="line violet-line"></div>
        </a>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <a class="card" href="?page=conference" target="_self">
            <div class="icon-circle green">📅</div>
            <div class="title-text">Conference Booking</div>
            <div class="line green-line"></div>
        </a>
        """,
        unsafe_allow_html=True
    )
