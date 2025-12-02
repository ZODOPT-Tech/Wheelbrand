import streamlit as st

def render_main_screen():
    """Renders the main selection screen for the application."""
    st.title("🐾 Welcome to ZODOPT MEETEASE 🤝")
    st.subheader("Please select your role to proceed.")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.header("👤 Visitor Access")
        st.info("For prospective adopters or general facility visitors.")
        if st.button("Visitor Login / Sign Up", key="main_visitor"):
            st.session_state['current_page'] = 'visitor_login'
            st.rerun()

    with col2:
        st.header("🗓️ Conference Access")
        st.info("For authorized personnel to manage conference room bookings.")
        if st.button("Conference Login", key="main_conference"):
            st.session_state['current_page'] = 'conference_login'
            st.rerun()

    st.markdown("---")
    st.caption("A ZODOPT Visitor Management System.")
