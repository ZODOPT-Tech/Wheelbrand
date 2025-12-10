import streamlit as st

# Import Modules
import main_screen
import visitor_login
import visitor_dashboard
import visitor_details
import visitor_identity
import conference_login
import conference_dashboard
import conference_booking

# --- Page Configuration ---
st.set_page_config(
    page_title="ZODOPT MEETEASE",
    layout="wide",
    page_icon="https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png",
    initial_sidebar_state="collapsed"
)

# --- Direct Function Router (Recommended) ---
PAGE_MODULES = {
    # Entry Point
    'main_screen': main_screen.render_main_screen,

    # VISITOR FLOW
    'visitor_login': visitor_login.render_visitor_login_page,
    'visitor_dashboard': visitor_dashboard.render_dashboard,
    'visitor_details': visitor_details.render_details_page,
    'visitor_identity': visitor_identity.render_identity_page,
    'visitor_pass': visitor_identity.render_pass_page,

    # CONFERENCE FLOW
    'conference_login': conference_login.render_conference_login_page,
    'conference_dashboard': conference_dashboard.render_dashboard,
    'conference_bookings': conference_booking.render_booking_page,
}


# --- Initialize Session ---
def initialize_session_state():
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'main_screen'


# --- Main Controller ---
def main():
    initialize_session_state()
    page_key = st.session_state['current_page']

    # Safe router
    func = PAGE_MODULES.get(page_key)

    if func:
        try:
            func()   # Direct call
        except Exception as e:
            st.error(f"Rendering Error in page '{page_key}': {e}")
    else:
        st.error(f"Page '{page_key}' not found in router.")
        if st.button("Back to Home"):
            st.session_state['current_page'] = 'main_screen'
            st.rerun()


if __name__ == "__main__":
    main()

