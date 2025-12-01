import streamlit as st
import base64
from pathlib import Path

# --- Configuration & State Initialization ---
st.set_page_config(layout="wide")
LOGO_PATH = "zodopt.png" 

if 'registration_step' not in st.session_state:
    st.session_state['registration_step'] = 'primary'
if 'visitor_data' not in st.session_state:
    st.session_state['visitor_data'] = {}

# --- Helper Functions (CSS and Header) ---

def img_to_base64(img_path):
    """Converts an image file to a base64 string for CSS embedding."""
    try:
        with open(img_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None

def render_custom_styles():
    """Applies custom CSS for the header banner and buttons."""
    logo_base64 = img_to_base64(LOGO_PATH)
    logo_css = ""
    if logo_base64:
        logo_css = f"""
        .zodopt-logo-container {{
            background-image: url("data:image/png;base64,{logo_base64}");
            background-size: contain;
            background-repeat: no-repeat;
            width: 40px; 
            height: 40px; 
            margin-left: 5px;
        }}
        """

    st.markdown(
        f"""
        <style>
        .header-banner {{
            background-color: #5d28a5; 
            color: white;
            padding: 10px 20px;
            font-size: 2em;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-radius: 5px;
            margin-bottom: 10px;
            width: 100%;
        }}
        .zodopt-tag {{
            display: flex;
            align-items: center;
            font-size: 0.5em;
        }}
        {logo_css}
        .step-tabs {{
            display: flex;
            margin-bottom: 20px;
        }}
        .step-tab {{
            padding: 10px 20px;
            cursor: default;
            font-weight: bold;
            color: #888;
            border-bottom: 3px solid transparent;
        }}
        .step-tab.active {{
            color: #5d28a5;
            border-bottom: 3px solid #5d28a5;
        }}
        /* Style for the "Next" button (Red/Pink from image) */
        div.stFormSubmitButton > button {{
            background-color: #ff545d; 
            color: white;
            border: none;
        }}
        /* Style for all standard st.button (used for Previous/Reset) */
        div.stButton > button {{ 
            background-color: white;
            color: #555;
            border: 1px solid #ccc;
        }}
        </style>
        """, 
        unsafe_allow_html=True
    )

def render_header(current_step):
    """Renders the header with the logo and step navigation."""
    render_custom_styles()
    st.markdown(
        f"""
        <div class="header-banner">
            VISITOR REGISTRATION
            <div class="zodopt-tag">
                <div class="zodopt-logo-container"></div>
                zodopt
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        f"""
        <div class="step-tabs">
            <div class="step-tab {'active' if current_step == 'primary' else ''}">PRIMARY DETAILS</div>
            <div class="step-tab {'active' if current_step == 'secondary' else ''}">SECONDARY DETAILS</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- Step 1: Primary Details Form ---

def render_primary_details_form():
    """Renders the Name, Phone, and Email form fields."""
    
    with st.container(border=False):
        
        with st.form("primary_details_form", clear_on_submit=False):
            # 1. Full Name
            st.write("Name *")
            full_name = st.text_input("Name", key="name_input", placeholder="Full Name", 
                                      value=st.session_state['visitor_data'].get('name', ''), 
                                      label_visibility="collapsed")

            # 2. Phone Number
            col_code, col_number = st.columns([1, 4])
            with col_code:
                st.write("Phone *", help="Country Code (default +91)")
                st.text_input("Country Code", value="+91", disabled=True, label_visibility="collapsed")
            with col_number:
                st.write("<br>", unsafe_allow_html=True)
                phone_number = st.text_input("Phone Number", key="phone_input", placeholder="81234 56789", 
                                             value=st.session_state['visitor_data'].get('phone', ''), label_visibility="collapsed")

            # 3. Email
            st.write("Email *")
            email = st.text_input("Email", key="email_input", placeholder="your.email@example.com", 
                                  value=st.session_state['visitor_data'].get('email', ''), label_visibility="collapsed")

            # Submit/Next and Reset buttons
            col_reset, col_spacer, col_next = st.columns([1, 2, 1])
            with col_reset:
                if st.button("Reset", use_container_width=True, key="reset_primary"):
                     for key in ['name', 'phone', 'email']:
                         st.session_state['visitor_data'].pop(key, None)
                     st.rerun()

            with col_next:
                if st.form_submit_button("Next →", use_container_width=True):
                    if not (full_name and phone_number and email):
                        st.error("⚠️ Please fill in all required fields (*).")
                    else:
                        st.session_state['visitor_data'].update({
                            'name': full_name,
                            'phone': phone_number,
                            'email': email
                        })
                        st.session_state['registration_step'] = 'secondary'
                        st.rerun()

# --- Step 2: Secondary Details Form (Dropdowns removed) ---

def render_secondary_details_form():
    """Renders the Other Details form fields with all dropdowns replaced by text inputs."""
    
    with st.container(border=False):
        st.markdown("### Other Details")

        # Define the button columns outside the form
        col_prev, col_next_container = st.columns(2)
        
        with col_prev:
            if st.button("Previous", key='prev_button_secondary', use_container_width=True):
                st.session_state['registration_step'] = 'primary'
                st.rerun()

        # The rest of the form fields and the submit button go inside st.form
        with st.form("secondary_details_form", clear_on_submit=False):
            
            # --- FORM FIELDS ---
            # 1. Company/Visit Details (Replaced SelectBoxes with Text Input)
            col_vt, col_fc = st.columns(2)
            with col_vt:
                st.text_input("Visit Type", key='visit_type', 
                             value=st.session_state['visitor_data'].get('visit_type', ''), 
                             placeholder="e.g., Business, Personal")
            with col_fc:
                st.text_input("From Company", key='from_company', 
                              value=st.session_state['visitor_data'].get('from_company', ''))
            
            col_dept, col_des = st.columns(2)
            with col_dept:
                st.text_input("Department", key='department',
                             value=st.session_state['visitor_data'].get('department', ''),
                             placeholder="e.g., Sales, HR, IT")
            with col_des:
                st.text_input("Designation", key='designation',
                             value=st.session_state['visitor_data'].get('designation', ''),
                             placeholder="e.g., Manager, Engineer")
            
            # 2. Organization Address Fields
            st.text_input("Organization Address", placeholder="Address Line 1", key='address_line_1',
                          value=st.session_state['visitor_data'].get('address_line_1', ''))
            
            col_city, col_state = st.columns(2)
            with col_city:
                st.text_input("City / District", key='city',
                              value=st.session_state['visitor_data'].get('city', ''))
            with col_state:
                st.text_input("State / Province", key='state',
                              value=st.session_state['visitor_data'].get('state', ''))
                
            col_postal, col_country = st.columns(2)
            with col_postal:
                st.text_input("Postal Code", key='postal_code',
                              value=st.session_state['visitor_data'].get('postal_code', ''))
            with col_country:
                st.text_input("Country", key='country',
                             value=st.session_state['visitor_data'].get('country', ''),
                             placeholder="e.g., India, USA")

            st.markdown("---") 
            
            # 3. Gender, Purpose, Person to Meet
            st.radio("Gender", ["Male", "Female", "Others"], horizontal=True, key='gender',
                     index=["Male", "Female", "Others"].index(st.session_state['visitor_data'].get('gender', 'Male')))
            
            col_purpose, col_person = st.columns(2)
            with col_purpose:
                st.text_input("Purpose", key='purpose',
                             value=st.session_state['visitor_data'].get('purpose', ''),
                             placeholder="e.g., Meeting, Interview")
            with col_person:
                st.text_input("Person to Meet", key='person_to_meet',
                             value=st.session_state['visitor_data'].get('person_to_meet', ''),
                             placeholder="e.g., Alice, Bob")
            
            # 4. Belongings (Checkboxes)
            st.markdown("#### Belongings")
            default_belongings = {
                'has_bags': False, 'has_documents': False, 'has_electronic_items': False,
                'has_laptop': False, 'has_charger': False, 'has_power_bank': False
            }
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.checkbox("Bags", key='has_bags', value=st.session_state['visitor_data'].get('has_bags', default_belongings['has_bags']))
                st.checkbox("Electronic Items", key='has_electronic_items', value=st.session_state['visitor_data'].get('has_electronic_items', default_belongings['has_electronic_items']))
                st.checkbox("Charger", key='has_charger', value=st.session_state['visitor_data'].get('has_charger', default_belongings['has_charger']))
            with col_b2:
                st.checkbox("Documents", key='has_documents', value=st.session_state['visitor_data'].get('has_documents', default_belongings['has_documents']))
                st.checkbox("Laptop", key='has_laptop', value=st.session_state['visitor_data'].get('has_laptop', default_belongings['has_laptop']))
                st.checkbox("Power Bank", key='has_power_bank', value=st.session_state['visitor_data'].get('has_power_bank', default_belongings['has_power_bank']))

            st.markdown("---")
            
            # --- SUBMISSION BUTTON ---
            with col_next_container:
                if st.form_submit_button("Next", use_container_width=True):
                    
                    # Update session_state['visitor_data'] with all current form values
                    st.session_state['visitor_data'].update({
                        'visit_type': st.session_state['visit_type'],
                        'from_company': st.session_state['from_company'],
                        'department': st.session_state['department'],
                        'designation': st.session_state['designation'],
                        'address_line_1': st.session_state['address_line_1'],
                        'city': st.session_state['city'],
                        'state': st.session_state['state'],
                        'postal_code': st.session_state['postal_code'],
                        'country': st.session_state['country'],
                        'gender': st.session_state['gender'],
                        'purpose': st.session_state['purpose'],
                        'person_to_meet': st.session_state['person_to_meet'],
                        'has_bags': st.session_state['has_bags'],
                        'has_documents': st.session_state['has_documents'],
                        'has_electronic_items': st.session_state['has_electronic_items'],
                        'has_laptop': st.session_state['has_laptop'],
                        'has_charger': st.session_state['has_charger'],
                        'has_power_bank': st.session_state['has_power_bank']
                    })
                    
                    st.balloons()
                    st.success("🎉 Visitor Registration Complete! Details have been recorded.")
                    st.session_state['registration_step'] = 'complete'
                    st.rerun() 

# --- Main Application Logic ---

def render_details_page():
    """Main function to run the multi-step visitor registration form."""
    
    render_header(st.session_state['registration_step'])

    if st.session_state['registration_step'] == 'primary':
        render_primary_details_form()
    
    elif st.session_state['registration_step'] == 'secondary':
        render_secondary_details_form()

    elif st.session_state['registration_step'] == 'complete':
        st.subheader("✅ Registration Summary")
        st.json(st.session_state['visitor_data'])
        
        st.markdown("---")
        if st.button("Start New Registration", type="primary"):
            st.session_state['registration_step'] = 'primary'
            st.session_state['visitor_data'] = {} 
            st.rerun()

if __name__ == "__main__":
    render_details_page()
