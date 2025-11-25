import streamlit as st
from PIL import Image

st.set_page_config(page_title="ZODOPT MEETEASE", layout="wide")

# Load logo
logo = Image.open("/mnt/data/logo.png")

# ---------------- HEADER STYLE ----------------
st.markdown("""
<style>
.header {
    width: 100%;
    padding: 30px 50px;
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
.logo-img {
    height: 80px;
}
.card {
    background-color: white;
    padding: 60px;
    border-radius: 25px;
    box-shadow: 0px 8px 20px rgba(0,0,0,0.08);
    text-align: center;
    width: 100%;
    transition: 0.2s ease-in-out;
    cursor: pointer;
    text-decoration: none !important;
    display: block;
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
.green { background: #00a884; }
.title-text { font-size: 24px; font-weight: 600; margin-top: 10px; }
.line {
    width: 60px;
    height: 6px;
    border-radius: 4px;
    margin: 12px auto 0 auto;
}
.violet-line { background: #b312ff; }
.green-line { background: #00a884; }
a { text-decoration: none; }
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
colH1, colH2 = st.columns([6, 1])

with colH1:
    st.markdown("""
    <div class="header">
        <div class="header-title">ZODOPT MEETEASE</div>
    </div>
    """, unsafe_allow_html=True)

with colH2:
    st.image(logo, width=120)

st.write("")  # spacing

# ---------------- BUTTONS ----------------
col1, col2 = st.columns(2, gap="large")

# Visitplan Card
with col1:
    st.markdown(
        """
        <a class="card" href="visit" target="_self">
            <div class="icon-circle violet">🗓️</div>
            <div class="title-text">Visitplan</div>
            <div class="line violet-line"></div>
        </a>
        """,
        unsafe_allow_html=True
    )

# Conference Card
with col2:
    st.markdown(
        """
        <a class="card" href="conference" target="_self">
            <div class="icon-circle green">📅</div>
            <div class="title-text">Conference Booking</div>
            <div class="line green-line"></div>
        </a>
        """,
        unsafe_allow_html=True
    )

