import streamlit as st

def render_dashboard():
    st.header("💻 Conference Dashboard")
    st.success("Welcome, Delegate!")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Registered", "1,240")
    col2.metric("Sessions Today", "8")
    col3.metric("Free Time Slots", "15")

    st.subheader("Manage Your Day")
    
    if st.button("🗓️ Manage Conference Bookings", type="primary", use_container_width=True):
        st.session_state['current_page'] = 'conference_bookings'
        st.rerun()
        
    st.write("---")
    if st.button("Logout"):
        st.session_state['current_page'] = 'conference_login'
        st.rerun()