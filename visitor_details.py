import streamlit as st

# --- Configuration ---
# Set the page configuration for better aesthetics
st.set_page_config(layout="wide")

# The path for the logo is 'zodopt.png'. 
# Ensure this image file is in the same directory as your Python script.
LOGO_PATH = "zodopt.png" 

# Initialize session state for navigation and data storage
if 'registration_step' not in st.session_state:
    st.session_state['registration_step'] = 'primary'
if 'visitor_data' not in st.session_state:
    st.session_state['visitor_data'] = {}


# --- Helper Functions ---

def render_custom_styles():
    """Applies custom CSS for the header banner and tabs."""
    st.markdown(
        """
        <style>
        /* Deep purple header banner */
        .header-banner {
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
        }
        /* Step navigation tabs */
        .step-tabs {
            display: flex;
            margin-bottom: 20px;
        }
        .step-tab {
            padding: 10px 20px;
            cursor: pointer;
            font-weight: bold;
            color: #888;
            border-bottom: 3px solid transparent;
        }
        .step-tab.active {
            color: #5d28a5;
            border-bottom: 3px solid #5d28a5;
        }
        /* Style for the "Next" button (Red/Pink from image) */
        div.stButton > button:first-child {
            background-color: #ff545d; /* Red/Pink color */
            color: white;
            border: none;
        }
        /* Style for the "Reset" and "Previous" buttons (secondary color) */
        div.stButton > button:last-child {
            border: 1px solid #ccc;
        }
        </style>
        """, 
        unsafe_allow_html=True
    )

def render_header(current_step):
    """Renders the header with the logo and step navigation."""
    
    # Render styles before the header content
    render_custom_styles()

    # Layout for Logo and Banner
    col_logo, col_banner = st.columns([1, 10])
    
    with col_logo:
        # Load the logo from the specified path (adjust width as needed)
        try:
            # We need to manually control the image placement/size 
            # as Streamlit columns can sometimes be tricky with custom sizing.
            st.image(LOGO_PATH, width=50) 
        except FileNotFoundError:
            # Fallback if the logo file isn't found
            st.markdown('<div style="color:#5d28a5; font-size:1.5em; font-weight:bold;">zodopt</div>', unsafe_allow_html=True)

    with col_banner:
        st.markdown(
            f'<div class="header-banner">VISITOR REGISTRATION <span style="font-size:0.5em; float:right;">zodopt</span></div>',
            unsafe_allow_html=True
        )

    # Render the step tabs (Primary/Secondary Details)
    st.markdown(
        f"""
        <div class="step-tabs">
            <div class="step-tab {'active' if current_step == 'primary' else ''}">PRIMARY DETAILS</div>
            <div class="step-tab {'active' if current_step == 'secondary' else ''}">SECONDARY DETAILS</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- Step 1: Primary Details ---

def render_primary_details_form():
    """Renders the Name, Phone, and Email form fields (image_4de6d2.png)."""
    
    st.markdown("### Primary Details")
    
    with st.form("primary_details_form", clear_on_submit=False):
        # 1. Full Name
        # Use st.container for a clean input box background (similar to the image)
        st.write("Name *")
        full_name = st.text_input("Name", key="name_input", placeholder="Full Name", 
                                  value=st.session_state['visitor_data'].get('name', ''), 
                                  label_visibility="collapsed")

        # 2. Phone Number (Split into Country Code and Number)
        st.write("Phone *")
        col_code, col_number = st.columns([1, 4])
        with col_code:
            st.text_input("Country Code", value="+91", disabled=True, label_visibility="collapsed")
        with col_number:
            phone_number = st.text_input("Phone Number", key="phone_input", placeholder="81234 56789", 
                                         value=st.session_state['visitor_data'].get('phone', ''), label_visibility="collapsed")

        # 3. Email
        st.write("Email *")
        email = st.text_input("Email", key="email_input", placeholder="your.email@example.com", 
                              value=st.session_state['visitor_data'].get('email', ''), label_visibility="collapsed")

        # Submit/Next and Reset buttons
        col_reset, col_spacer, col_next = st.columns([1, 2, 1])
        with col_reset:
            if st.form_submit_button("Reset", type="secondary", use_container_width=True):
                 # Simple reset: clear current inputs and session state data for this step
                 st.session_state['visitor_data'].update({'name': '', 'phone': '', 'email': ''})
                 st.rerun() # Rerun to reflect the cleared state

        with col_next:
            if st.form_submit_button("Next →", type="primary", use_container_width=True):
                if not (full_name and phone_number and email):
                    st.error("⚠️ Please fill in all required fields (*).")
                else:
                    # Save data and move to the next step
                    st.session_state['visitor_data'].update({
                        'name': full_name,
                        'phone': phone_number,
                        'email': email
                    })
                    st.session_state['registration_step'] = 'secondary'
                    st.rerun()
    
# --- Step 2: Secondary Details (Other Details) ---

def render_secondary_details_form():
    """Renders the Other Details form fields (image_4de676.png)."""
    
    st.markdown("### Secondary Details (Other Details)")

    # Use a form to capture all data for this step
    with st.form("secondary_details_form", clear_on_submit=False):
        
        # 1. Company/Visit Details
        col_vt, col_fc = st.columns(2)
        with col_vt:
            st.selectbox("Visit Type", ["-Select-", "Business", "Personal", "Other"], key='visit_type',
                         index=["-Select-", "Business", "Personal", "Other"].index(st.session_state['visitor_data'].get('visit_type', "-Select-")))
        with col_fc:
            st.text_input("From Company", key='from_company', 
                          value=st.session_state['visitor_data'].get('from_company', ''))
        
        col_dept, col_des = st.columns(2)
        with col_dept:
            st.selectbox("Department", ["-Select-", "Sales", "IT", "HR"], key='department',
                         index=["-Select-", "Sales", "IT", "HR"].index(st.session_state['visitor_data'].get('department', "-Select-")))
        with col_des:
            st.selectbox("Designation", ["-Select-", "Manager", "Engineer", "Director"], key='designation',
                         index=["-Select-", "Manager", "Engineer", "Director"].index(st.session_state['visitor_data'].get('designation', "-Select-")))
        
        # 2. Organization Address
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
            st.selectbox("Country", ["-Select-", "India", "USA", "Other"], key='country',
                         index=["-Select-", "India", "USA", "Other"].index(st.session_state['visitor_data'].get('country', "-Select-")))

        # 3. Gender, Purpose, Person to Meet
        st.radio("Gender", ["Male", "Female", "Others"], horizontal=True, key='gender',
                 index=["Male", "Female", "Others"].index(st.session_state['visitor_data'].get('gender', 'Male')))
        
        col_purpose, col_person = st.columns(2)
        with col_purpose:
            st.selectbox("Purpose", ["-Select-", "Meeting", "Interview", "Delivery"], key='purpose',
                         index=["-Select-", "Meeting", "Interview", "Delivery"].index(st.session_state['visitor_data'].get('purpose', "-Select-")))
        with col_person:
            st.selectbox("Person to Meet", ["-Select-", "Alice", "Bob", "Charlie"], key='person_to_meet',
                         index=["-Select-", "Alice", "Bob", "Charlie"].index(st.session_state['visitor_data'].get('person_to_meet', "-Select-")))
        
        # 4. Belongings (Checkboxes)
        st.markdown("#### Belongings")
        
        # Pre-set default values for belongings to avoid key errors later
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
        
        # Previous and Next/Submit buttons
        col_prev, col_next = st.columns(2)
        
        with col_prev:
            # Use a standard button for 'Previous' to change step without submitting the form
            if st.button("Previous", key='prev_button', use_container_width=True, 
                         type="secondary"):
                st.session_state['registration_step'] = 'primary'
                st.rerun()

        with col_next:
            if st.form_submit_button("Next", type="primary", use_container_width=True):
                
                # Save ALL data from session state keys used in this form
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
                
                # Final submission/completion logic
                st.balloons()
                st.success("🎉 Visitor Registration Complete! Details have been recorded.")
                st.session_state['registration_step'] = 'complete'
                st.rerun() 

# --- Main Application Logic (Renamed as requested) ---

def render_details_page():
    """
    Main function to run the multi-step visitor registration form.
    NOTE: This function name matches the one expected by your configuration.
    """
    
    # Render the header based on the current step
    render_header(st.session_state['registration_step'])

    # Conditional rendering based on the current step
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
            st.session_state['visitor_data'] = {} # Clear data for new start
            st.rerun()

if __name__ == "__main__":
    render_details_page()
