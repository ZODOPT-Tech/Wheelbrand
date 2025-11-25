import streamlit as st
from PIL import Image
import base64
from io import BytesIO

st.set_page_config(page_title="ZODOPT MEETEASE", layout="wide")

# -------------- HEADER --------------
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
    width: 100%;
    cursor: pointer;
    display: block;
    text-decoration: none !important;
}
.card:hover {
    transform: translateY(-5px);
    box-shadow: 0px 12px 25px rgba(0,0,0,0.12);
}
.icon-circle {
    width: 110px; height: 110px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 20px auto;
    font-size: 40px; color: white;
}
.violet { background: linear-gradient(135deg,#4d7cff,#b312ff); }
.green { background: #00a884; }
.title-text { font-size: 24px; font-weight: 600; }
.line { width: 60px; height: 6px; border-radius: 4px; margin: 12px auto 0 auto; }
.violet-line { background:#b312ff; }
.green-line { background:#00a884; }
</style>
""", unsafe_allow_html=True)

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

# -------------- BUTTONS --------------
col1, col2 = st.columns(2, gap="large")

with col1:
    # Visit plan
    if st.button("Visit Plan", key="visit", use_container_width=True):
        st.switch_page("pages/visitor.py")

    st.markdown(
        """
        <div class="card">
            <div class="icon-circle violet">🗓️</div>
            <div class="title-text">Visitplan</div>
            <div class="line violet-line"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    # Conference
    if st.button("Conference", key="conf", use_container_width=True):
        st.switch_page("pages/conference.py")

    st.markdown(
        """
        <div class="card">
            <div class="icon-circle green">📅</div>
            <div class="title-text">Conference Booking</div>
            <div class="line green-line"></div>
        </div>
        """,
        unsafe_allow_html=True
    )
