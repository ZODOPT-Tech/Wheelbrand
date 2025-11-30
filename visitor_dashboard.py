import streamlit as st

def render_dashboard():
    st.header("📊 Visitor Dashboard")
    st.success("You are logged in.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("Identity Card")
        st.write("View your digital ID for site access.")
        if st.button("View Identity Card"):
            st.session_state['current_page'] = 'visitor_identity'
            st.rerun()
            
    with col2:
        st.info("Personal Details")
        st.write("Review or update your visit information.")
        if st.button("Edit Details"):
            st.session_state['current_page'] = 'visitor_details'
            st.rerun()

    st.write("---")
    if st.button("Logout"):
        st.session_state['current_page'] = 'visitor_login'
        st.rerun()