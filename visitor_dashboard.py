import streamlit as st

def render_dashboard():
    """
    Renders the main dashboard for a logged-in visitor/staff.
    Allows navigation to register a new visitor or log out.
    """
    # Assuming visitor data is stored in session state upon visitor login
    visitor_name = st.session_state.get('visitor_name', 'Guest')
    
    # Simplified main heading, similar to visitor_login.py
    st.header("Dashboard")
    st.markdown("---")

    st.markdown(f"## 👋 Welcome Back, {visitor_name}")
    st.success("You are successfully checked in and logged in.")
    st.write("Use the controls below to manage the system or register a new guest.")
    st.markdown('<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)

    # Navigation to the details module (New Visitor Registration)
    st.subheader("Visitor Registration")
    st.info("Click the button below to start the check-in process for a new visitor.")
    
    # Button updated to "NEW VISITOR"
    if st.button("NEW VISITOR", type="primary", use_container_width=True):
        # Navigates to the 'visitor_details' page
        st.session_state['current_page'] = 'visitor_details'
        st.rerun()

    st.markdown('<div style="margin-top: 40px;"></div>', unsafe_allow_html=True)
    
    # Logout functionality
    st.subheader("Session Management")
    if st.button("← Logout", key="visitor_dashboard_logout_btn", use_container_width=True):
        # Clear visitor session state data
        if 'visitor_logged_in' in st.session_state:
            del st.session_state['visitor_logged_in']
        # Navigate back to the login page
        st.session_state['current_page'] = 'visitor_login' 
        st.rerun()
