import streamlit as st

LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


def render_page_header(title: str, back_page: str = None):
    st.markdown("""
    <style>
        /* Remove default header */
        header[data-testid="stHeader"] {
            display: none !important;
        }

        /* Make Streamlit main container flush to top */
        .block-container {
            padding-top: 0rem !important;
        }

        .app-header {
            background: %s;
            padding: 16px 30px;
            margin: 0px -1rem 2rem -1rem;
            border-radius: 0 0 16px 16px;
            box-shadow: 0 5px 14px rgba(0,0,0,0.16);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-left, .header-center, .header-right {
            display: flex;
            align-items: center;
        }

        .header-center {
            flex: 1;
            justify-content: center;
        }

        .header-title {
            font-size: 28px;
            font-weight: 800;
            color: white;
            font-family: 'Inter', sans-serif;
            letter-spacing: 0.8px;
            text-align: center;
        }

        .back-btn {
            background: rgba(255,255,255,0.20);
            border: none;
            color: white;
            padding: 6px 16px;
            font-size: 15px;
            border-radius: 8px;
            cursor: pointer;
        }

        .back-btn:hover {
            background: rgba(255,255,255,0.28);
        }

        .avatar-img {
            height: 40px;
            width: 40px;
            border-radius: 50%;
            border: 2px solid rgba(255,255,255,0.65);
        }
    </style>
    """ % HEADER_GRADIENT, unsafe_allow_html=True)

    st.markdown("<div class='app-header'>", unsafe_allow_html=True)

    # LEFT
    st.markdown("<div class='header-left'>", unsafe_allow_html=True)
    if back_page:
        if st.button("← Back", key="back_top_btn"):
            st.session_state['current_page'] = back_page
            st.rerun()
    else:
        # Invisible placeholder to maintain layout
        st.markdown("<div style='width:70px;'></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # CENTER
    st.markdown("<div class='header-center'>", unsafe_allow_html=True)
    st.markdown(f"<div class='header-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # RIGHT
    st.markdown("<div class='header-right'>", unsafe_allow_html=True)
    st.markdown(f"<img src='{LOGO_URL}' class='avatar-img'>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)



def render_dashboard():
    # perfect header
    render_page_header("CONFERENCE DASHBOARD")

    # welcome
    user = st.session_state.get("user_name", "Delegate")
    st.success(f"Welcome, {user}!")

    st.write("---")

    # metrics
    bookings = st.session_state.get("bookings", [])
    today_count = 0

    col1, col2 = st.columns(2)
    col1.metric("Total Bookings", len(bookings))
    col2.metric("Today's Bookings", today_count)

    st.write("---")

    st.subheader("Your Actions")

    if st.button("🗓️ Manage Conference Bookings", type="primary", use_container_width=True):
        st.session_state['current_page'] = 'conference_bookings'
        st.rerun()

    st.write("---")

    if st.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.session_state['current_page'] = 'conference_login'
        st.rerun()
