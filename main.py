import streamlit as st

# =====================================================
# IMPORT ALL PAGE MODULES
# =====================================================
try:
    import main_screen
    import visitor_login
    import visitor_dashboard
    import visitor_primarydetails
    import visitor_secondarydetails
    import visitor_identity
    import conference_login
    import conference_dashboard
    import conference_booking
except Exception as e:
    st.error(f"Module Import Error: {e}")
    st.stop()


# =====================================================
# STREAMLIT PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="ZODOPT MEETEASE",
    layout="wide",
    page_icon="https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png",
    initial_sidebar_state="collapsed"
)


# =====================================================
# PAGE ROUTER CONFIG
# =====================================================
PAGE_MODULES = {
    # ---------------- MAIN ----------------
    'main_screen': main_screen.render_main_screen,

    # ---------------- VISITOR FLOW ----------------
    'visitor_login': visitor_login.render_visitor_login_page,
    'visitor_dashboard': visitor_dashboard.render_dashboard,
    'visitor_primarydetails': visitor_primarydetails.render_primary_form,
    'visitor_secondarydetails': visitor_secondarydetails.render_secondary_form,
    'visitor_identity': visitor_identity.render_identity_page,
    'visitor_pass': visitor_identity.render_pass_page,

    # ---------------- CONFERENCE FLOW ----------------
    'conference_login': conference_login.render_conference_login_page,
    'conference_dashboard': conference_dashboard.render_dashboard,
    'conference_bookings': conference_booking.render_booking_page,
}


# =====================================================
# SESSION INITIALIZATION
# =====================================================
def initialize_session_state():
    defaults = {
        "current_page": "main_screen",
        "visitor_data": {},
        "registration_step": "primary",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =====================================================
# MAIN ROUTER CONTROLLER
# =====================================================
def main():
    initialize_session_state()

    current_page = st.session_state.get("current_page", "main_screen")
    render_function = PAGE_MODULES.get(current_page)

    if render_function is None:
        st.error(f"⛔ Page '{current_page}' not found in router.")

        if st.button("Back to Home"):
            st.session_state["current_page"] = "main_screen"
            st.rerun()
        return

    try:
        render_function()

    except Exception as e:
        st.error(f"⚠ Error while rendering '{current_page}': {e}")

        if st.checkbox("Show Technical Details"):
            st.exception(e)

        if st.button("Go to Home Screen"):
            st.session_state["current_page"] = "main_screen"
            st.rerun()


# =====================================================
# RUN APP
# =====================================================
if __name__ == "__main__":
    main()
