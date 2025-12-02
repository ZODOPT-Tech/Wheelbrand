import streamlit as st

def render_visitor_login_page():
    """Renders the visitor login/sign-up page."""
    st.title("👤 Visitor Login")
    st.markdown("Please enter your details to sign in or register.")

    # A simple form simulation
    email = st.text_input("Email Address", key="v_login_email")
    password = st.text_input("Password", type="password", key="v_login_pass")

    if st.button("Login"):
        # **SIMULATION:** In a real app, you would check credentials against a database.
        if email and password:
            st.session_state['user_email'] = email
            st.session_state['is_logged_in'] = True
            st.session_state['current_page'] = 'visitor_dashboard'
            st.success("Login successful! Redirecting...")
            st.rerun()
        else:
            st.error("Please enter both email and password.")
            
    if st.button("Back to Main Screen"):
        st.session_state['current_page'] = 'main_screen'
        st.rerun()
