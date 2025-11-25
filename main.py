import streamlit as st

st.set_page_config(page_title="Home", layout="wide")

# --- Styles ---
st.markdown("""
<style>
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

# --- Layout ---
col1, col2 = st.columns(2, gap="large")

# --- Visitplan Card ---
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

# --- Conference Booking Card ---
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
