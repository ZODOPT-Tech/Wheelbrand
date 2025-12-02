import streamlit as st

def render_details_page():
    """Renders the visitor's details update page."""
    st.title("📝 Visitor Details Update")
    st.write("This is where the visitor can edit their personal information.")
    
    st.text_input("Full Name")
    st.text_area("Address")
    
    if st.button("Save Details"):
        st.success("Details saved successfully! (Simulation)")
        
    st.markdown("---")
    if st.button("Back to Dashboard"):
        st.session_state['current_page'] = 'visitor_dashboard'
        st.rerun()
