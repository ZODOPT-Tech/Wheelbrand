import streamlit as st

# ---------------------------------------------------------
# Custom CSS (matches your UI screenshot)
# ---------------------------------------------------------
def load_css():
    st.markdown("""
    <style>

    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        max-width: 1500px !important;
    }

    /* HEADER BAR */
    .header-bar {
        width: 100%;
        background: linear-gradient(90deg, #2356F6, #5A38F9, #8A23FF);
        padding: 45px 70px;
        border-radius: 35px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 60px;
    }

    .header-title {
        font-size: 42px;
        font-weight: 800;
        color: white;
        letter-spacing: 1px;
    }

    /* ZODOPT LOGO IMAGE */
    .logo-img {
        height: 60px;
        object-fit: contain;
    }

    /* CARDS */
    .option-card {
        background: white;
        border-radius: 22px;
        padding: 25px;
        height: 420px;
        text-align: center;
        box-shadow: 0px 8px 28px rgba(0,0,0,0.08);
        position: relative;
    }

    .icon-circle {
        width: 200px;
        height: 200px;
        border-radius: 50%;
        margin: 45px auto 30px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 95px;
        color: white;
    }

    .calendar-icon {
        background: linear-gradient(45deg, #5A4BFF, #A53CFF);
    }

    .book-icon {
        background: #00a884;
    }

    .stButton>button {
        width: 100%;
        background: #1A5CFF !important;
        color: white !important;
        border: none !important;
        padding: 18px 0 !important;
        border-radius: 12px !important;
        font-size: 20px !important;
        font-weight: 600 !important;
    }

    .stButton>button:hover {
        background: #004de6 !important;
    }

    </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# MAIN PAGE
# ---------------------------------------------------------
def render_main_screen():

    load_css()

    # ------------------ HEADER BAR -----------------------
    st.markdown('<div class="header-bar">', unsafe_allow_html=True)

    # Left: Title
    st.markdown('<div class="header-title">ZODOPT MEETEASE</div>', unsafe_allow_html=True)

    # Right: Logo image (PNG)
    st.image("zodopt.png", width=160)

    st.markdown("</div>", unsafe_allow_html=True)

    # ------------------ CARD SECTION ----------------------
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<div class="option-card">', unsafe_allow_html=True)
        st.markdown('<div class="icon-circle calendar-icon">📅</div>', unsafe_allow_html=True)

        if st.button("Visit Plan", key="btn_visit_plan"):
            st.session_state.current_page = "visitor_login"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="option-card">', unsafe_allow_html=True)
        st.markdown('<div class="icon-circle book-icon">📚</div>', unsafe_allow_html=True)

        if st.button("Conference Booking", key="btn_conference_booking"):
            st.session_state.current_page = "conference_login"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    st.caption("A ZODOPT Visitor and Conference Management System.")


# ------------------ RENDER PAGE --------------------------
render_main_screen()
