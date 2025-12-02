import streamlit as st
import importlib

# --- Import Page Modules ---
# NOTE: These modules must exist as separate .py files in the same directory.
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

---

# --- Session State Initialization (CRUCIAL CHANGE) ---
def initialize_session_state():
    """
    Initializes session state variables *only if* they don't exist yet (first load).
    This allows the application to maintain state and navigate pages without
    resetting to the main screen on every single rerun.
    """
    if 'current_page' not in st.session_state:
        # This only runs on the very first load or explicit browser refresh (F5).
        # Ensures the application always starts at the main_screen.
        st.session_state['current_page'] = PAGE_MAIN
        st.session_state['is_logged_in'] = False 
        st.session_state['user_role'] = None     
        st.session_state['user_data'] = {}       
    
    # Optional: If you want to force a state clear on a browser refresh,
    # you can keep the previous logic, but that defeats SPA navigation.
    # The current logic is better for a multi-page app feel.

---

# --- Main Application Logic (Router) ---
def main():
    # 1. Page Configuration (Must be the first Streamlit command)
    st.set_page_config(
        page_title="ZODOPT MEETEASE", 
        layout="wide",
        initial_sidebar_state="collapsed" 
    )

    # 2. Initialize State (Only runs on first load)
    initialize_session_state()

    # 3. Get Current Page Info
    page_key: str = st.session_state.get('current_page', PAGE_MAIN)
    page_info = PAGE_MODULES.get(page_key)

    # 4. Authentication Guard
    if page_info and page_info.get('auth_required', False) and not st.session_state['is_logged_in']:
        # If the current page requires auth but the user is logged out,
        # redirect to the appropriate login page.
        st.warning("🔒 Session expired or unauthorized access. Redirecting to login.")
        st.session_state['current_page'] = PAGE_V_LOGIN if page_key.startswith('visitor') else (PAGE_C_LOGIN if page_key.startswith('conference') else PAGE_MAIN)
        st.rerun()
        
    # 5. Render Page
    if page_info:
        try:
            # Dynamically get the render function from the imported module
            render_func = getattr(page_info['module'], page_info['func'])
            
            # Pass navigate_to to page modules so they can trigger navigation
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
