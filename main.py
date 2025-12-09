import streamlit as st

# --- Import Page Modules ---
# Import all required Python files/modules
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

# --- Page Configuration ---
st.set_page_config(
    page_title="ZODOPT MEETEASE", 
    layout="wide",
    # Set the browser tab icon (favicon) using a URL 
    page_icon="https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png", 
    initial_sidebar_state="collapsed" 
)

# --- Navigation Dictionary (Using Finalized Function Names) ---
# This dictionary maps the page keys used in st.session_state['current_page'] to the 
# correct module and function to render that page.
PAGE_MODULES = {
    # Entry Point
    'main_screen': {'module': main_screen, 'func': 'render_main_screen'},

    # --- VISITOR FLOW ---
    'visitor_login': {'module': visitor_login, 'func': 'render_visitor_login_page'},
    'visitor_dashboard': {'module': visitor_dashboard, 'func': 'render_dashboard'},
    'visitor_details': {'module': visitor_details, 'func': 'render_details_page'},
    'visitor_identity': {'module': visitor_identity, 'func': 'render_identity_page'},
    
    # --- CONFERENCE FLOW (Corrected Function Name) ---
    # The function name MUST match the definition in conference_login.py
    'conference_login': {'module': conference_login, 'func': 'render_conference_login_page'}, 
    'conference_dashboard': {'module': conference_dashboard, 'func': 'render_dashboard'},
    'conference_bookings': {'module': conference_booking, 'func': 'render_booking_page'},
}

def initialize_session_state():
    """Ensures all necessary session state variables are initialized."""
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'main_screen'
    
    # Initialize flow-specific variables to prevent errors on first load
    # if 'user_email' not in st.session_state:
    #     st.session_state['user_email'] = None 
    # if 'conf_auth_view' not in st.session_state:
    #     st.session_state['conf_auth_view'] = 'login'

def main():
    # 1. Initialize State
    initialize_session_state()

    # 2. Get Current Page Info
    page_key = st.session_state['current_page']

    # 3. Render Page
    if page_key in PAGE_MODULES:
        page_info = PAGE_MODULES[page_key]
        
        # Dynamically calls the correct rendering function (e.g., main_screen.render_main_screen())
        try:
            render_func = getattr(page_info['module'], page_info['func'])
            render_func()
        except AttributeError:
            st.error(f"Configuration Error: Function '{page_info['func']}' not found in module '{page_info['module'].__name__}'. Please check the function name.")
            if st.button("Go to Main Screen"):
                st.session_state['current_page'] = 'main_screen'
                st.rerun()

    else:
        st.error(f"Navigation Error: Page key '{page_key}' is not defined.")
        if st.button("Reset to Main Screen"):
            st.session_state['current_page'] = 'main_screen'
            st.rerun()

if __name__ == "__main__":
    main()
