import streamlit as st

def render_login_page():
    st.header("👤 Visitor Login")
    st.markdown("Welcome back! Please sign in.")

    with st.form("visitor_login_form"):
        username = st.text_input("Visitor ID / Email")
        password = st.text_input("Password", type="password")
        
        submitted = st.form_submit_button("Login")
        
        if submitted:
            # Dummy Auth: Check if a username was entered
            if username and password == "123": 
                st.session_state['current_page'] = 'visitor_dashboard'
                st.rerun()
            else:
                st.error("Invalid ID or Password. Try ID/Pass: test/123")

    st.divider()
    if st.button("← Back to Main"):
        st.session_state['current_page'] = 'main_screen'
        st.rerun