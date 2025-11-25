import streamlit as st
# Import page content functions
from main_screen import main_dashboard
from visitor import visitor_management
from conference import conference_room_booking

def navigate_to(page_name):
    """Updates the session state to change the current page."""
    st.session_state['current_page'] = page_name

def app_navigator():
    """Renders the appropriate function based on the current_page state."""
    page = st.session_state['current_page']

    if page == 'main':
        main_dashboard()
    elif page == 'visitor':
        visitor_management()
    elif page == 'conference':
        conference_room_booking()
    else:
        st.error("Page not found. Returning to main dashboard.")
        navigate_to('main')