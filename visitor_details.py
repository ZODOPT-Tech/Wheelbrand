import streamlit as st
import time # Used for simulating processing delay

# --- Utility Function for Header (Copied for consistency) ---
def render_header():
    """Renders the custom header similar to the ZODOPT MEETEAZE banner."""
    
    # Custom CSS to create the purple-blue gradient banner effect and style
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;800&display=swap');
            
            .zodopt-header {
                background: linear-gradient(to right, #4A148C, #8C2CFE); /* Purple to Blue Gradient */
                color: white;
                padding: 15px 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }
            .zodopt-title-text {
                font-family: 'Poppins', sans-serif;
                font-size: 24px;
                font-weight: 800;
                letter-spacing: 1px;
                margin: 0;
            }
            .zodopt-logo-text {
                font-family: 'Poppins', sans-serif;
                font-size: 24px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }
            .zodopt-logo-red { color: #FF4B4B; }
            .zodopt-logo-blue { color: #4059A1; }
            
            /* Overriding Streamlit's default header margin */
            .stApp > header { display: none; }
            
            /* Styles for step navigation */
            .step-container {
                display: flex;
                margin-bottom: 20px;
                border-bottom: 3px solid #E0E0E0;
            }
            .step {
                padding: 10px 20px;
                text-align: center;
                cursor: pointer;
                border-bottom: 3px solid transparent;
                font-weight: bold;
                color: #616161;
            }
            .active-step {
                color: #4A148C;
                border-bottom: 3px solid #4A148C !important;
            }
        </style>
        <div class="zodopt-header">
            <h1 class="zodopt-title-text">VISITOR REGISTRATION</h1>
            <div class="zodopt-logo-text">
                <span class="zodopt-logo-red">zo</span><span class="zodopt-logo-blue">dopt</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_identity_page():
    """Renders the Identity Capture and Finalization step for the visitor flow."""
    render_header()
    
    # Custom HTML for the tab-like navigation (Identity is the third logical step)
    st.markdown("""
    <div class="step-container">
        <div class="step" style="color: #9E9E9E;">PRIMARY DETAILS</div>
        <div class="step" style="color: #9E9E9E;">SECONDARY DETAILS</div>
        <div class="step active-step">IDENTITY & CHECK-IN</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("📸 Visitor Identity Capture")
    st.info("Please capture your photograph and upload a valid ID for security purposes.")

    with st.form("identity_form"):
        col_photo, col_id = st.columns(2)

        with col_photo:
            st.markdown("##### Take Photo")
            # Streamlit provides a native camera input widget
            camera_image = st.camera_input("Visitor Photograph", label_visibility="collapsed")
            if camera_image:
                st.session_state['visitor_photo'] = camera_image

        with col_id:
            st.markdown("##### Upload ID Document")
            # File uploader for ID
            uploaded_file = st.file_uploader(
                "Upload Valid ID (e.g., Driver's License, Passport)", 
                type=["pdf", "jpg", "jpeg", "png"],
                key="id_uploader",
                label_visibility="collapsed"
            )
            if uploaded_file:
                st.session_state['visitor_id'] = uploaded_file

        st.markdown("---")
        st.checkbox("I agree to the Terms and Conditions and Privacy Policy.", key="agree_terms")
        st.markdown("---")

        col_prev, col_submit = st.columns(2)
        
        with col_prev:
            # Button to go back to the previous step (visitor_details)
            if st.form_submit_button("← Previous", key="prev_identity_submit", use_container_width=True, type="secondary"):
                # Use st.session_state['current_page'] for navigation back to visitor_details
                st.session_state['current_page'] = 'visitor_details'
                st.rerun()

        with col_submit:
            # Final submission and check-in button
            if st.form_submit_button("Final Check-In", key="checkin_submit", use_container_width=True, type="primary"):
                if 'visitor_photo' in st.session_state and st.session_state.agree_terms:
                    with st.spinner('Processing and registering visitor...'):
                        time.sleep(2) # Simulate processing time
                    
                    st.success("Check-In Complete! You are registered.")
                    st.balloons()
                    
                    # Navigate to the dashboard or a completion page defined in main.py
                    st.session_state['current_page'] = 'visitor_dashboard'
                    st.rerun()
                elif not st.session_state.agree_terms:
                    st.error("You must agree to the Terms and Conditions to proceed.")
                else:
                    st.error("Please capture your photo to complete registration.")

# Note: The main application logic will be handled by your 'main.py' file.
