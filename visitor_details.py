import streamlit as st

def render_details_page():
    st.subheader("📝 Update Visitor Details")
    
    with st.form("details_form"):
        st.text_input("Full Name", value="John Visitor")
        st.text_area("Purpose of Visit", value="Project Review Meeting")
        st.date_input("Planned Departure Date")
        
        if st.form_submit_button("Save Changes"):
            st.toast("Details successfully updated!")

    st.divider()
    if st.button("← Back to Dashboard"):
        st.session_state['current_page'] = 'visitor_dashboard'
        st.rerun()