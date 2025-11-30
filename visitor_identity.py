import streamlit as st

def render_identity_page():
    st.header("🆔 Digital Identity Card")
    
    st.warning("Please present this ID at all checkpoints.")
    
    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image("https://via.placeholder.com/100", caption="Photo ID")
        with col2:
            st.markdown("### **VISITOR ID: V-998822**")
            st.markdown("**Name:** John Visitor")
            st.markdown("**Access Level:** General Access")
            st.markdown("**Expiration:** Nov 30, 2025")
            st.success("STATUS: VALID")

    st.divider()
    if st.button("← Back to Dashboard"):
        st.session_state['current_page'] = 'visitor_dashboard'
        st.rerun()