import streamlit as st

def render_dashboard():
    """Renders the main dashboard for a logged-in visitor."""
    # Check if a user is logged in (basic guard)
    if 'is_logged_in' not in st.session_state or not st.session_state['is_logged_in']:
        st.warning("Please log in to view the dashboard.")
        st.session_state['current_page'] = 'visitor_login'
        st.rerun()
        return

    st.title(f"👋 Welcome, Visitor!")
    st.markdown(f"**Email:** `{st.session_state.get('user_email', 'N/A')}`")

    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📝 Update Details")
        st.info("Update your contact and profile information.")
        if st.button("Go to Details", key="dash_details"):
            st.session_state['current_page'] = 'visitor_details'
            st.rerun()

    with col2:
        st.subheader("🆔 Verify Identity")
        st.info("Upload required documents for adoption/visit pre-approval.")
        if st.button("Go to Identity", key="dash_identity"):
            st.session_state['current_page'] = 'visitor_identity'
            st.rerun()
            
    with col3:
        st.subheader("⬅️ Logout")
        st.error("End your current session.")
        if st.button("Logout", key="dash_logout"):
            # Clear all flow-specific state variables upon logout
            for key in ['user_email', 'is_logged_in']:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state['current_page'] = 'main_screen'
            st.rerun()
