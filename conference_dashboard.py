import streamlit as st
from datetime import datetime

# ---------------------------------------------------------
# GLOBAL CONFIG
# ---------------------------------------------------------
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


# ---------------------------------------------------------
# HEADER COMPONENT
# ---------------------------------------------------------
def render_page_header(title: str, back_page: str = None):
    # Inject UI CSS
    st.markdown(f"""
    <style>
        /* Hide default Streamlit bar */
        header[data-testid="stHeader"] {{
            display: none !important;
        }}

        /* Move content up */
        .block-container {{
            padding-top: 0rem !important;
        }}

        /* Header Container */
        .app-header {{
            background: {HEADER_GRADIENT};
            padding: 16px 30px;
            margin: 0px -1rem 2rem -1rem;
            border-radius: 0 0 16px 16px;
            box-shadow: 0 5px 14px rgba(0,0,0,0.16);
            
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .header-left, .header-center, .header-right {{
            display: flex;
            align-items: center;
        }}

        .header-center {{
            flex: 1;
            justify-content: center;
        }}

        .header-title {{
            font-size: 28px;
            font-weight: 800;
            color: #fff;
            font-family: 'Inter', sans-serif;
            letter-spacing: 1px;
            text-align: center;
        }}

        .back-btn {{
            background: rgba(255, 255, 255, 0.22);
            border: none;
            color: white;
            padding: 6px 16px;
            font-size: 15px;
            border-radius: 8px;
            cursor: pointer;
        }}

        .back-btn:hover {{
            background: rgba(255, 255, 255, 0.30);
        }}

        .avatar-img {{
            height: 38px;
            width: 38px;
            border-radius: 50%;
            border: 2px solid rgba(255,255,255,0.7);
        }}
    </style>

    <div class="app-header">
        <div class="header-left">
    """, unsafe_allow_html=True)

    # LEFT | Back Button or placeholder
    if back_page:
        if st.button("← Back", key="header_back_btn"):
            st.session_state['current_page'] = back_page
            st.rerun()
    else:
        # Keep layout centered
        st.markdown("<div style='width:70px;'></div>", unsafe_allow_html=True)

    # CENTER | Title
    st.markdown(f"""
        </div>
        <div class="header-center">
            <div class="header-title">{title}</div>
        </div>
        <div class="header-right">
            <img src="{LOGO_URL}" class="avatar-img">
        </div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# DASHBOARD PAGE
# ---------------------------------------------------------
def render_dashboard():
    # No back button here
    render_page_header("CONFERENCE DASHBOARD")

    # Welcome
    username = st.session_state.get("user_name", "Delegate")
    st.success(f"Welcome, **{username}**!")

    st.write("---")

    # Bookings summary
    bookings = st.session_state.get("bookings", [])
    today_date = datetime.today().date()
    today_count = 0
    if bookings:
        today_count = len([b for b in bookings if b['start'].date() == today_date])

    col1, col2 = st.columns(2)
    col1.metric("Total Bookings", len(bookings))
    col2.metric("Today's Bookings", today_count)

    st.write("---")

    st.subheader("Your Actions")

    # Go to bookings
    if st.button("🗓️ Manage Conference Bookings", type="primary", use_container_width=True):
        st.session_state['current_page'] = 'conference_bookings'
        st.rerun()

    st.write("---")

    # Logout
    if st.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.session_state['current_page'] = 'conference_login'
        st.rerun()
