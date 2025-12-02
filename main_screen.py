import streamlit as st

# ----------------------------------------
# Custom CSS (exact look of your reference UI)
# ----------------------------------------
def load_css():
    st.markdown("""
    <style>

    /* Remove Streamlit default paddings */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        max-width: 1400px;
    }

    /* TOP HEADER BAR */
    .header-bar {
        width: 100%;
        background: linear-gradient(90deg, #2356F6, #713CFC, #8A23FF);
        padding: 40px 60px;
        border-radius: 30px;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 60px;
    }

    .header-title {
        font-size: 42px;
        font-weight: 700;
        color: white;
    }

    /* ZODOPT LOGO TEXT */
    .zodopt-logo span.z { color: #ff1a0a; }
    .zodopt-logo span.o1 { color: #ff661a; }
    .zodopt-logo span.d { color: #00b36b; }
    .zodopt-logo span.o2 { color: #0073e6; }
    .zodopt-logo span.p { color: #3366ff; }
    .zodopt-logo span.t { color: #a64dff; }

    .zodopt-logo {
        font-size: 42px;
        font-weight: 900;
    }

    /* CARD */
    .option-card {
        background: white;
        border-radius: 20px;
        padding: 30px;
        height: 400px;
        text-align: center;
        box-shadow: 0px 8px 30px rgba(0,0,0,0.08);
        position: relative;
    }

    /* ICON BIG CIRCLE */
    .icon-circle {
        width: 200px;
        height: 200px;
        border-radius: 50%;
        margin: 40px auto 20px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 90px;
        color: white;
    }

    .calendar-icon {
        background: linear-gradient(45deg, #5A4BFF, #A53CFF);
    }

    .book-icon {
        background: #00a884;
    }

    /* BUTTON FULL WIDTH */
    .stButton>button {
        width: 100%;
        background: #1A5CFF;
        color: white;
        border: none;
        padding: 18px 0;
        border-radius: 12px;
        font-size: 20px;
        font-weight: 600;
    }
    .stButton>button:hover {
        background: #004de6;
    }

    </style>
    """, unsafe_allow_html=True)


# ----------------------------------------
# MAIN UI LAYOUT
# ----------------------------------------
def render_main_screen():

    load_css()

    # ---------- HEADER ----------
    st.markdown("""
    <div class="header-bar">
        <div class="header-title">ZODOPT MEETEASE</div>
        <div class="zodopt-logo">
            <span class="z">z</span><span class="o1">o</span><span class="d">d</span><span class="o2">o</span><span class="p">p</span><span class="t">t</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------- 2 CARDS ----------
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<div class="option-card">', unsafe_allow_html=True)
        st.markdown('<div class="icon-circle calendar-icon">📅</div>', unsafe_allow_html=True)
        if st.button("Visit Plan"):
            st.session_state.current_page = "visitor_login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="option-card">', unsafe_allow_html=True)
        st.markdown('<div class="icon-circle book-icon">📚</div>', unsafe_allow_html=True)
        if st.button("Conference Booking"):
            st.session_state.current_page = "conference_login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.caption("A ZODOPT Visitor and Conference Management System.")


# Call the function (for testing)
render_main_screen()
