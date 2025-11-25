import streamlit as st

st.set_page_config(page_title="Home", layout="wide")

st.markdown("""
<style>
.box {
    background-color: white;
    padding: 60px;
    border-radius: 25px;
    box-shadow: 0px 8px 20px rgba(0,0,0,0.08);
    text-align: center;
    cursor: pointer;
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
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    if st.button(" ", key="visitplan_btn"):
        st.switch_page("visit.py")

    st.markdown("""
    <div class="box" onclick="document.querySelector('button[kind=primary]').click()">
        <div class="icon-circle violet">
            🗓️
        </div>
        <div class="title-text">Visitplan</div>
        <div class="line violet-line"></div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if st.button(" ", key="conference_btn"):
        st.switch_page("conference.py")

    st.markdown("""
    <div class="box" onclick="document.querySelector('button[kind=secondary]').click()">
        <div class="icon-circle green">
            📅
        </div>
        <div class="title-text">Conference Booking</div>
        <div class="line green-line"></div>
    </div>
    """, unsafe_allow_html=True)
