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

# Initialize step state
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = 1
# Initialize data state to store form values across steps
if 'visitor_data' not in st.session_state:
    st.session_state['visitor_data'] = {}

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

def render_navigation():
    """Renders the step navigation tabs using markdown and custom CSS."""
    
    # Define the steps and their labels
    steps = {
        1: "PRIMARY DETAILS",
        2: "SECONDARY DETAILS",
        3: "IDENTITY"
    }

    # Generate the navigation HTML
    nav_html = '<div class="tab-navigation">'
    for step_num, label in steps.items():
        is_active = "active" if st.session_state['current_step'] == step_num else ""
        # Using a div and handling clicks visually via state changes in the full app
        # For a Streamlit component, this is the safest way to render styled tabs
        nav_html += f"""
        <div class="tab-item {is_active}">
            {label}
        </div>
        """
    nav_html += '</div>'
    st.markdown(nav_html, unsafe_allow_html=True)

def render_step_1_primary_details():
    """Renders Step 1: Primary Details (Name, Contact)."""
    with st.form("step_1_form"):
        st.markdown("<p style='font-size: 16px; color: #555; margin-bottom: 20px;'>Provide your essential contact information.</p>", unsafe_allow_html=True)
        
        # Primary Fields (Full Name, Phone, Email - All Mandatory)
        col_name, col_phone = st.columns(2)
        
        with col_name:
            full_name = st.text_input("Full Name *", key="reg_full_name", 
                                      value=st.session_state['visitor_data'].get('full_name', ''), 
                                      placeholder="Enter your full name")
            
        with col_phone:
            # Simplified phone input, country code logic is simulated
            st.markdown("<label style='font-size: 14px; font-weight: 600;'>Phone Number *</label>", unsafe_allow_html=True)
            col_code, col_num = st.columns([1, 3])
            with col_code:
                st.selectbox("Code", options=["+91", "+1", "+44"], label_visibility="collapsed", key="reg_phone_code",
                             index=["+91", "+1", "+44"].index(st.session_state['visitor_data'].get('phone_code', '+91')))
            with col_num:
                phone_number = st.text_input("Number", key="reg_phone_number", label_visibility="collapsed", 
                                             value=st.session_state['visitor_data'].get('phone_number', ''), 
                                             placeholder="81234 56789")
            
        email = st.text_input("Email *", key="reg_email", 
                              value=st.session_state['visitor_data'].get('email', ''), 
                              placeholder="your.email@example.com")
        
        # NOTE: Company Name removed from here as per request.

        st.markdown('<div style="margin-top: 30px; text-align: right;">', unsafe_allow_html=True)
        if st.form_submit_button("Next →", type="primary"):
            # Required fields validation (All are mandatory now)
            phone_code = st.session_state.get('reg_phone_code', '+91')
            required_fields = [full_name, phone_number, email]
            if all(required_fields):
                # Save data to session state
                st.session_state['visitor_data'].update({
                    'full_name': full_name,
                    'phone_code': phone_code,
                    'phone_number': phone_number,
                    'email': email,
                })
                st.session_state['current_step'] = 2
                st.rerun()
            else:
                st.error("Please fill in all primary details marked with *.")
        st.markdown('</div>', unsafe_allow_html=True)

def render_step_2_secondary_details():
    """Renders Step 2: Secondary Details (Company, Visit Info, Host, Belongings)."""
    with st.form("step_2_form"):
        st.markdown("<p style='font-size: 16px; color: #555; margin-bottom: 20px;'>Details regarding your organization and visit plan.</p>", unsafe_allow_html=True)
        
        # **NEW: Company Name is now here**
        company = st.text_input("Company Name *", key="reg_company", 
                                value=st.session_state['visitor_data'].get('company', ''))
        
        st.markdown("---")
        st.markdown("##### Visit Details")
        
        # Visit Type and Purpose
        col_type, col_purpose = st.columns(2)
        with col_type:
             visit_type = st.selectbox("Visit Type *", options=["Business", "Interview", "Delivery", "Personal"], 
                                      key="reg_visit_type", 
                                      index=["Business", "Interview", "Delivery", "Personal"].index(st.session_state['visitor_data'].get('visit_type', 'Business')))
        with col_purpose:
            purpose = st.selectbox("Purpose *", options=["Project Review", "Meeting", "Inspection", "Other"],
                                  key="reg_purpose_visit", 
                                  index=["Project Review", "Meeting", "Inspection", "Other"].index(st.session_state['visitor_data'].get('purpose', 'Project Review')))
            
        # Dates
        col_arrival, col_departure = st.columns(2)
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        
        with col_arrival:
            arrival_date = st.date_input("Planned Arrival Date *", key="reg_arrival_date", 
                                         value=st.session_state['visitor_data'].get('arrival_date', today))
        with col_departure:
            departure_date = st.date_input("Planned Departure Date *", key="reg_departure_date", 
                                           value=st.session_state['visitor_data'].get('departure_date', tomorrow))

        st.markdown("---")
        st.markdown("##### Host Details")
        
        # Host Details
        col_host_name, col_host_email = st.columns(2)
        with col_host_name:
            host_name = st.text_input("Host/Contact Person Name *", key="reg_host_name", 
                                      value=st.session_state['visitor_data'].get('host_name', ''))
        with col_host_email:
            host_email = st.text_input("Host/Contact Person Email *", key="reg_host_email", 
                                       value=st.session_state['visitor_data'].get('host_email', ''))

        # Belongings
        st.markdown("---")
        st.markdown("##### Belongings")
        belongings = st.multiselect("Items you are bringing inside:", 
                                    options=['Laptop', 'Electronic Items', 'Documents', 'Bags', 'Power Bank'],
                                    default=st.session_state['visitor_data'].get('belongings', []))

        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.form_submit_button("← Previous", type="secondary"):
                st.session_state['current_step'] = 1
                st.rerun()
        
        with col_next:
            if st.form_submit_button("Next →", type="primary"):
                # Required fields validation (All marked with * are mandatory)
                required_fields = [company, visit_type, purpose, arrival_date, departure_date, host_name, host_email]
                if all(required_fields):
                    # Save data to session state
                    st.session_state['visitor_data'].update({
                        'company': company,
                        'visit_type': visit_type,
                        'purpose': purpose,
                        'arrival_date': arrival_date,
                        'departure_date': departure_date,
                        'host_name': host_name,
                        'host_email': host_email,
                        'belongings': belongings,
                    })
                    st.session_state['current_step'] = 3
                    st.rerun()
                else:
                    st.error("Please fill in all secondary details marked with *.")


def render_step_3_identity():
    """Renders Step 3: Identity (Photo and ID upload placeholder)."""
    with st.form("step_3_form"):
        st.markdown("<p style='font-size: 16px; color: #555; margin-bottom: 20px;'>Complete the verification process by providing your photo identification.</p>", unsafe_allow_html=True)
        
        # Identity Fields
        st.info("Identity verification is required for access. Please upload or capture your details.")
        
        # Placeholder for Photo Upload
        col_photo, col_id = st.columns(2)
        with col_photo:
            st.camera_input("Take a photo of yourself (for badge) *", key="reg_photo")
        with col_id:
            st.file_uploader("Upload Government ID (e.g., Driver's License) *", type=['pdf', 'jpg', 'png'], key="reg_id_upload")
        
        # Final Submission
        st.markdown("---")
        
        col_prev, col_submit = st.columns(2)
        with col_prev:
            if st.form_submit_button("← Previous", type="secondary"):
                st.session_state['current_step'] = 2
                st.rerun()

        with col_submit:
            if st.form_submit_button("Finalize & Register", type="primary"):
                # Check that final steps (photo/ID) are completed (simplified check for now)
                # We need to explicitly check if the file_uploader and camera_input keys have values
                is_photo_uploaded = st.session_state.get('reg_photo') is not None
                is_id_uploaded = st.session_state.get('reg_id_upload') is not None
                
                if is_photo_uploaded and is_id_uploaded:
                    # Final save and transition
                    st.toast("Registration Complete! Welcome.")
                    
                    # You would usually save the final data (including photo/ID) to Firestore here
                    
                    st.session_state['current_page'] = 'visitor_dashboard' 
                    st.rerun()
                else:
                    st.error("Please provide a photo and upload an ID to finalize registration.")


def render_details_page():
    """Renders the main Visitor Registration page with header and multi-step form."""
    
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
        margin-bottom: 0px; 
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

    /* Navigation Tab Styling */
    .tab-navigation {{
        display: flex;
        justify-content: space-between;
        width: 100%;
        margin-bottom: 25px;
        border-bottom: 2px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); 
        background-color: #FFFFFF;
    }}

    .tab-item {{
        flex-grow: 1;
        text-align: center;
        padding: 18px 0;
        font-weight: 600;
        color: #999;
        cursor: default; 
        transition: all 0.2s ease;
        border-bottom: 3px solid transparent;
        font-size: 16px;
        letter-spacing: 0.5px;
    }}

    .tab-item.active {{
        color: #50309D; /* Primary color */
        border-bottom: 3px solid #50309D; 
        background-color: #f0f0f4;
    }}


    /* Form Container Styling */
    .details-form-container {{
        background: #f7f7f9;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        max-width: 700px;
        margin: 30px auto 30px auto; /* Center the form */
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
        width: 100% !important;
        transition: all 0.2s ease;
    }}
    .stForm button[kind="primary"]:hover {{
        opacity: 0.95;
        transform: translateY(-2px);
    }}
    
    .stForm button[kind="secondary"] {{
        background: #e0e0e0 !important;
        color: #555 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 20px !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        width: 100% !important;
        transition: all 0.2s ease;
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
    .stTextInput input, .stTextArea textarea, .stDateInput input, .stSelectbox [data-testid="stSelectbox"] {{
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 8px;
        padding: 10px 15px;
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
    
    # --- 3. Navigation Tabs ---
    # The header bar from the image has the tabs right below it, without extra padding
    st.markdown(f'<div style="padding: 0;">', unsafe_allow_html=True)
    render_navigation()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # --- 4. Content Area & Form Rendering ---
    
    # Wrap form in the styled container and apply padding here
    st.markdown('<div class="details-form-container">', unsafe_allow_html=True)

    if st.session_state['current_step'] == 1:
        render_step_1_primary_details()
    elif st.session_state['current_step'] == 2:
        render_step_2_secondary_details()
    elif st.session_state['current_step'] == 3:
        render_step_3_identity()
    
    # Close the form container
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="text-align: center; margin-top: 30px; padding-bottom: 20px;">', unsafe_allow_html=True)
    
    # Back button logic (outside the form flow)
    if st.button("← Back to Dashboard", key="back_to_dashboard"):
        if 'current_page' in st.session_state:
            st.session_state['current_page'] = 'main' # Assuming 'main' is the selection screen
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)


# --- Application Entry Point ---
# Ensures the function can be called by the main app router
if __name__ == '__main__':
    # Initialize session state if running this file directly for testing
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'registration'
        
    render_details_page()
