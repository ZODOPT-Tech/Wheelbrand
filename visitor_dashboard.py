import streamlit as st

def render_dashboard():
    """
    Renders the main dashboard for a logged-in visitor.
    Allows navigation to view personal details.
    """
    # Assuming visitor data is stored in session state upon visitor login
    visitor_name = st.session_state.get('visitor_name', 'Guest')
    
    st.markdown(f"## 👋 Welcome Back, {visitor_name}")
    st.header("📊 Visitor Dashboard Status")
    
    st.success("You are successfully checked in and logged in.")
    st.write("Use the links below to access site information and manage your visit details.")
    st.markdown("---")
    
    # Navigation to the details module
    st.info("Personal Visit Details")
    st.write("Review or update your active visit information and personal data.")
    
    # This button triggers the navigation to the 'visitor_details' module/page
    if st.button("Manage My Details →", type="primary", use_container_width=True):
        # Corrected: Use 'current_page' for routing as defined in main.py
        st.session_state['current_page'] = 'visitor_details'
        st.rerun()

    st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
    
    # Logout functionality (adjust session state keys as needed for the visitor flow)
    if st.button("← Logout", key="visitor_dashboard_logout_btn"):
        # Clear visitor session state data
        if 'visitor_logged_in' in st.session_state:
            del st.session_state['visitor_logged_in']
        # Corrected: Use 'current_page' and the correct target page 'visitor_login'
        st.session_state['current_page'] = 'visitor_login' 
        st.rerun()
