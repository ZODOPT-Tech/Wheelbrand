import streamlit as st

# --- Import Page Modules ---
# Import all required Python files/modules (These files must exist in the same directory)
import main_screen
import visitor_login
import visitor_dashboard
import visitor_details
import visitor_identity
import conference_login
import conference_dashboard
import conference_booking

# Note: If you created app_styles.py, you would import it here:
# import app_styles 

# --- Constants for Page Keys ---
PAGE_MAIN = 'main_screen'
PAGE_V_LOGIN = 'visitor_login'
PAGE_V_DASH = 'visitor_dashboard'
PAGE_C_LOGIN = 'conference_login'
PAGE_C_DASH = 'conference_dashboard'

# --- Navigation Dictionary (Maps key to module and render function) ---
PAGE_MODULES = {
    # Entry Point
    PAGE_MAIN: {'module': main_screen, 'func': 'render_main_screen'},

    # --- VISITOR FLOW ---
    PAGE_V_LOGIN: {'module': visitor_login, 'func': 'render_visitor_login_page'},
    PAGE_V_DASH: {'module': visitor_dashboard, 'func': 'render_dashboard'},
    'visitor_details': {'module': visitor_details, 'func': 'render_details_page'},
    'visitor_identity': {'module': visitor_identity, 'func': 'render_identity_page'},
    
    # --- CONFERENCE FLOW ---
    PAGE_C_LOGIN: {'module': conference_login, 'func': 'render_conference_login_page'}, 
    PAGE_C_DASH: {'module': conference_dashboard, 'func': 'render_dashboard'},
    'conference_bookings': {'module': conference_booking, 'func': 'render_booking_page'},
}

def navigate_to(page_key: str):
    """Updates the session state to change the currently rendered page."""
    if page_key in PAGE_MODULES:
        st.session_state['current_page'] = page_key
        st.rerun()
    else:
        # Should not happen if the page key comes from PAGE_MODULES
        st.error(f"Invalid navigation target: {page_key}")


def initialize_session_state():
    """Ensures all necessary session state variables are initialized."""
    # The key that controls which page is rendered
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = PAGE_MAIN
    
    # --- Authentication/User State ---
    if 'is_logged_in' not in st.session_state:
        st.session_state['is_logged_in'] = False # True/False
    if 'user_role' not in st.session_state:
        st.session_state['user_role'] = None # e.g., 'visitor' or 'conference_admin'
    if 'user_data' not in st.session_state:
        st.session_state['user_data'] = {} # Stores user-specific data after login (e.g., name, ID, email)


def main():
    # 1. Page Configuration (Must be the first Streamlit command)
    st.set_page_config(
        page_title="ZODOPT MEETEASE", 
        layout="wide",
        initial_sidebar_state="collapsed" 
    )

    # 2. Initialize State
    initialize_session_state()

    # 3. Get Current Page Info
    page_key = st.session_state['current_page']

    # 4. Render Page
    if page_key in PAGE_MODULES:
        page_info = PAGE_MODULES[page_key]
        
        # Dynamically calls the correct rendering function (e.g., main_screen.render_main_screen())
        try:
            render_func = getattr(page_info['module'], page_info['func'])
            
            # Call the function to render the page content
            render_func()
            
        except AttributeError:
            # Handle cases where the function name in PAGE_MODULES is wrong
            st.error(
                f"🚨 Configuration Error: Function **'{page_info['func']}'** "
                f"not found in module **'{page_info['module'].__name__}'**."
                f"Please check the function name in `PAGE_MODULES`."
            )
            if st.button("Go to Main Screen", key="error_to_main"):
                navigate_to(PAGE_MAIN)
    else:
        # Handle cases where the session state has an invalid page key
        st.error(f"❌ Navigation Error: Page key **'{page_key}'** is not defined.")
        if st.button("Reset to Main Screen", key="invalid_key_to_main"):
            navigate_to(PAGE_MAIN)

if __name__ == "__main__":
    main()
