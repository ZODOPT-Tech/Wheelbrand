import streamlit as st
import os
import base64
import datetime

# --- Configuration (Copied from visitor.py for consistency) ---
LOGO_PATH = "zodopt.png" 
LOGO_PLACEHOLDER_TEXT = "zodopt"
# Primary Color: Purple/Indigo gradient
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)" 
APP_PADDING_X = "2rem"

# Utility function to convert image to base64 for embedding
def _get_image_base64(path):
    """Converts a local image file to a base64 string for embedding in HTML/CSS."""
    try:
        if os.path.exists(path):
            with open(path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
        # Fallback placeholder data (a small purple square)
        return "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDTAgAQJUYAKYfBpZZXFw5AAAAAElFTkSuQmCC"
    except Exception:
        return ""

def render_details_page():
    """Renders the Visitor Registration/Update Details Page with consistent styling."""
    
    # --- 1. Custom CSS for Styling ---
    st.markdown(f"""
    <style>
    /* Global Streamlit Overrides to ensure full width and no margins */
    html, body {{
        font-family: 'Inter', sans-serif; 
    }}
    .stApp .main .block-container,
    .css-18e3th9, 
    .css-1rq2lgs {{ 
        padding: 0 !important;
        max-width: 100% !important; 
        margin: 0 !important;
    }}
    .stApp > header {{ visibility: hidden; }}

    /* Header Box (Matching the style of the main app) */
    .header-box {{
        background: {HEADER_GRADIENT};
        padding: 20px {APP_PADDING_X};
        margin-top: 0px; 
        margin-bottom: 40px;
        border-radius: 0; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%; 
        margin: 0; 
    }}
    
    .header-title-inner {{
        font-family: 'Inter', sans-serif; 
        font-size: 34px;
        font-weight: 800;
        color: #FFFFFF; 
        letter-spacing: 1.5px;
        margin: 0;
    }}

    /* Form Container Styling */
    .details-form-container {{
        background: #f7f7f9;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        max-width: 700px;
        margin: 0 auto 30px auto; /* Center the form */
    }}

    /* Primary Button Style (Using the gradient) */
    .stForm button[kind="primary"] {{
        background: {HEADER_GRADIENT} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 20px !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 10px rgba(80, 48, 157, 0.4) !important;
        margin-top: 15px !important; 
        width: 100% !important;
        transition: all 0.2s ease;
    }}
    .stForm button[kind="primary"]:hover {{
        opacity: 0.95;
        transform: translateY(-2px);
    }}

    /* Back Button Style */
    .stButton > button[key="back_to_dashboard"] {{
        background: #FFFFFF !important; 
        color: #555555 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        border: 1px solid #E0E0E0 !important;
        font-weight: 500 !important;
        padding: 8px 15px !important;
        margin-top: 10px !important;
        font-size: 16px !important;
    }}

    /* Input Styling */
    .stTextInput input, .stTextArea textarea, .stDateInput input {{
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 8px;
        padding: 12px 15px;
        font-size: 16px;
    }}

    </style>
    """, unsafe_allow_html=True)

    # --- 2. Header ---
    header_title = "VISITOR REGISTRATION"
    logo_base64 = _get_image_base64(LOGO_PATH)
    if logo_base64:
        logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="header-logo-img" style="height: 50px; border-radius: 8px;">'
    else:
        logo_html = f'<div class="header-logo-container">**{LOGO_PLACEHOLDER_TEXT}**</div>'

    st.markdown(
        f"""
        <div class="header-box">
            <div class="header-title-inner">{header_title}</div> 
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # --- 3. Content Area with Padding ---
    st.markdown(f'<div style="padding: 0 {APP_PADDING_X};">', unsafe_allow_html=True)
    
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 25px;">
            <h1 style="font-size: 28px; color: #50309D; font-weight: 700;">Please fill in your details</h1>
            <p style="color: #666;">Complete the required fields for your visit plan.</p>
        </div>
        """, unsafe_allow_html=True
    )
    
    # Wrap form in the styled container
    st.markdown('<div class="details-form-container">', unsafe_allow_html=True)

    # --- 4. Registration Form ---
    with st.form("visitor_registration_form"):
        # Primary Details (similar to image_bf177e.png)
        st.markdown("### Primary Details")
        col_name, col_phone = st.columns(2)
        
        with col_name:
            # Removed 'value' placeholder to simulate fresh registration
            full_name = st.text_input("Full Name *", key="reg_full_name")
            
        with col_phone:
            # Simple phone input for now, but in a real app, this would use the country code dropdown
            phone_number = st.text_input("Phone Number *", key="reg_phone_number") 
            
        email = st.text_input("Email *", key="reg_email")
        company = st.text_input("Company Name *", key="reg_company")

        st.markdown("---")
        st.markdown("### Visit Details")
        
        # Visit specific details
        purpose = st.text_area("Purpose of Visit *", key="reg_purpose_visit", height=100)
        
        col_dates, col_host = st.columns(2)
        
        with col_dates:
            # Default to today's date for arrival and +1 day for departure
            today = datetime.date.today()
            arrival_date = st.date_input("Planned Arrival Date *", value=today, key="reg_arrival_date")
            departure_date = st.date_input("Planned Departure Date *", value=today + datetime.timedelta(days=1), key="reg_departure_date")
            
        with col_host:
            # Assuming the visitor needs to specify who they are meeting
            host_name = st.text_input("Host/Contact Person Name *", key="reg_host_name")
            host_email = st.text_input("Host/Contact Person Email *", key="reg_host_email")

        st.markdown("---")
        
        submitted = st.form_submit_button("Submit Registration", type="primary")

        if submitted:
            # Basic validation
            required_fields = [full_name, phone_number, email, company, purpose, arrival_date, departure_date, host_name, host_email]
            if all(required_fields):
                st.toast("Registration details submitted successfully! Redirecting...")
                
                # In a real app, you would save these details to Firestore/DB here.
                # Example: save_visitor_data(data)
                
                # Transition to the next stage, e.g., showing a confirmation or the visitor dashboard
                st.session_state['current_page'] = 'visitor_dashboard' 
                st.rerun()
            else:
                st.error("Please fill in all fields marked with *.")
    
    # Close the form container and the main content wrapper
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="text-align: center; margin-top: 30px; padding-bottom: 20px;">', unsafe_allow_html=True)
    
    # Back button logic (Ensure session state is initialized if this file is run standalone)
    if st.button("← Back to Dashboard", key="back_to_dashboard"):
        if 'current_page' in st.session_state:
            st.session_state['current_page'] = 'main' # Assuming 'main' is the selection screen
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# --- Application Entry Point ---
# Ensures the function can be called by the main app router
if __name__ == '__main__':
    # Initialize session state if running this file directly for testing
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'registration'
        
    render_details_page()
