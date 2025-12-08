import streamlit as st

# ---------------------------------------------------------
# GLOBAL CONFIG
# ---------------------------------------------------------
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


# ---------------------------------------------------------
# HEADER COMPONENT
# ---------------------------------------------------------
def render_page_header(title: str, back_page: str = None):
    st.markdown(f"""
    <style>
        header[data-testid="stHeader"] {{
            visibility: hidden;
            height: 0px;
        }}

        .app-main-header {{
            background: {HEADER_GRADIENT};
            padding: 18px 35px;
            margin: -1rem -1rem 2rem -1rem;
            border-radius: 0 0 18px 18px;
            box-shadow: 0 5px 14px rgba(0,0,0,0.18);
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            align-items: center;
        }}

        .header-back {{
            text-align: left;
        }}

        .header-title {{
            text-align: center;
            font-size: 30px;
            font-weight: 800;
            color: white;
            letter-spacing: 1px;
            font-family: 'Inter', sans-serif;
        }}

        .header-avatar {{
            text-align: right;
        }}

        .avatar-img {{
            height: 46px;
            width: 46px;
            border-radius: 50%;
            border: 2px solid rgba(255,255,255,0.65);
        }}
    </style>

    <div class="app-main-header">
        <div class="header-back">
    """, unsafe_allow_html=True)

    # Back button only if page is specified
    if back_page:
        if st.button("← Back", key="header_back_btn"):
            st.session_state['current_page'] = back_page
            st.rerun()

    st.markdown(f"""
        </div>
        <div class="header-title">{title}</div>
        <div class="header-avatar">
            <img src="{LOGO_URL}" class="avatar-img">
        </div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# DASHBOARD PAGE
# ---------------------------------------------------------
def render_dashboard():
    # Dashboard header (no back button here)
    render_page_header("CONFERENCE DASHBOARD")

    # Welcome message
    username = st.session_state.get("user_name", "Delegate")
    st.success(f"Welcome, {username}!")

    # Bookings data (if stored in session)
    bookings = st.session_state.get("bookings", [])
    today = len([b for b in bookings if b['start'].date() == st.session_state.get("today_date", None)])

    # Metrics
    col1, col2 = st.columns(2)
    col1.metric("Total Bookings", len(bookings))
    col2.metric("Today's Bookings", today)

    st.write("---")

    st.subheader("Your Actions")

    # Go to booking page
    if st.button("🗓️ Manage Conference Bookings", type="primary", use_container_width=True):
        st.session_state['current_page'] = 'conference_bookings'
        st.rerun()

    st.write("---")

    # Logout
    if st.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.session_state['current_page'] = 'conference_login'
        st.rerun()
