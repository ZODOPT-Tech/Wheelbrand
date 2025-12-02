import streamlit as st
import importlib

# --- Import Page Modules ---
import main_screen
import visitor_login
import visitor_dashboard
import visitor_details
import visitor_identity
import conference_login
import conference_dashboard
import conference_booking

# --- Constants for Page Keys ---
PAGE_MAIN = 'main_screen'
PAGE_V_LOGIN = 'visitor_login'
PAGE_V_DASH = 'visitor_dashboard'
PAGE_C_LOGIN = 'conference_login'
PAGE_C_DASH = 'conference_dashboard'

# --- Navigation Dictionary (Maps key to module, render function, and auth requirement) ---
PAGE_MODULES = {
    # Entry Point
    PAGE_MAIN: {'module': main_screen, 'func': 'render_main_screen', 'auth_required': False},

    # --- VISITOR FLOW ---
    PAGE_V_LOGIN: {'module': visitor_login, 'func': 'render_visitor_login_page', 'auth_required': False},
    PAGE_V_DASH: {'module': visitor_dashboard, 'func': 'render_dashboard', 'auth_required': True},
    'visitor_details': {'module': visitor_details, 'func': 'render_details_page', 'auth_required': True},
    'visitor_identity': {'module': visitor_identity, 'func': 'render_identity_page', 'auth_required': True},
    
    # --- CONFERENCE FLOW ---
    PAGE_C_LOGIN: {'module': conference_login, 'func': 'render_conference_login_page', 'auth_required': False}, 
    PAGE_C_DASH: {'module': conference_dashboard, 'func': 'render_dashboard', 'auth_required': True},
    'conference_bookings': {'module': conference_booking, 'func': 'render_booking_page', 'auth_required': True},
}

# --- Core Navigation Function ---
def navigate_to(page_key: str):
    """Updates the session state to change the currently rendered page and reruns."""
    if page_key in PAGE_MODULES:
        # Check if the page is restricted and the user is not logged in
        if PAGE_MODULES[page_key].get('auth_required', False) and not st.session_state.get('is_logged_in', False):
             # Redirect to login page for the appropriate role if known, otherwise main
             st.session_state['current_page'] = PAGE_V_LOGIN if page_key.startswith('visitor') else (PAGE_C_LOGIN if page_key.startswith('conference') else PAGE_MAIN)
        else:
            st.session_state['current_page'] = page_key
        st.rerun()
    else:
        st.error(f"⚠️ **Developer Error**: Invalid navigation target: `{page_key}`. Page key not found in `PAGE_MODULES`.")

# --- Session State Initialization (FORCED RESET ON REFRESH) ---
def initialize_session_state():
    """
    Clears all existing session state variables and re-initializes
    only the necessary default variables to force a reset upon every
    browser refresh or rerun.
    """
    
    # 🚨 CLEAR ALL STATE 🚨
    # Use list() to avoid dictionary size changes during iteration
    for key in list(st.session_state.keys()):
        del st.session_state[key]
        
    # --- Re-Initialize Default State ---
    st.session_state['current_page'] = PAGE_MAIN
    st.session_state['is_logged_in'] = False 
    st.session_state['user_role'] = None     
    st.session_state['user_data'] = {}       


# --- Main Application Logic (Router) ---
def main():
    # 1. Page Configuration (Must be the first Streamlit command)
    st.set_page_config(
        page_title="ZODOPT MEETEASE", 
        layout="wide",
        initial_sidebar_state="collapsed" 
    )

    # 2. Initialize State (This is where the reset occurs on every run)
    initialize_session_state()

    # 3. Get Current Page Info
    page_key: str = st.session_state.get('current_page', PAGE_MAIN)
    page_info = PAGE_MODULES.get(page_key)

    # 4. Authentication Guard (Ensures a proper redirect if the default PAGE_MAIN isn't login)
    if page_info and page_info.get('auth_required', False) and not st.session_state['is_logged_in']:
        # This guard is technically redundant now because initialize_session_state
        # always sets the page key to PAGE_MAIN and login status to False, but
        # it is good practice to keep for robust routing logic.
        st.warning("🔒 Session expired or unauthorized access. Redirecting to login.")
        st.session_state['current_page'] = PAGE_V_LOGIN
        st.rerun()
        
    # 5. Render Page
    if page_info:
        try:
            render_func = getattr(page_info['module'], page_info['func'])
            
            # Pass navigate_to to page modules
            render_func(navigate_to=navigate_to) 
            
        except AttributeError:
            st.error(
                f"🚨 Configuration Error: Function **'{page_info['func']}'** "
                f"not found in module **'{page_info['module'].__name__}'**."
            )
            if st.button("Go to Main Screen", key="error_to_main"):
                navigate_to(PAGE_MAIN)
                
        except ImportError as e:
            st.error(f"❌ Critical Import Error: Could not load module for page '{page_key}'. Details: {e}")
            if st.button("Reset Application", key="import_error_reset"):
                navigate_to(PAGE_MAIN)

    else:
        st.error(f"❌ Navigation Error: Page key **'{page_key}'** is not defined in `PAGE_MODULES`.")
        if st.button("Reset to Main Screen", key="invalid_key_to_main"):
            navigate_to(PAGE_MAIN)

if __name__ == "__main__":
    main()
