import streamlit as st

# --- Configuration ---
# Set the page configuration for better aesthetics
st.set_page_config(layout="wide")

# The path for the logo is 'zodopt.png'. Assuming it's in the same directory.
LOGO_PATH = "zodopt.png" 

# Initialize session state for navigation and data storage
if 'registration_step' not in st.session_state:
    st.session_state['registration_step'] = 'primary'
if 'visitor_data' not in st.session_state:
    st.session_state['visitor_data'] = {}


def render_header(current_step):
    """Renders the header with the logo and step navigation."""
    
    # Custom styling to recreate the purple header banner from the image
    st.markdown(
        """
        <style>
        .header-banner {
            background-color: #5d28a5; /* Deep purple */
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
        </style>
        """, 
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 10])
    
    with col1:
        # Load the logo from the specified path
        try:
            st.image(LOGO_PATH, width=50) # You might need to adjust width
        except FileNotFoundError:
            # Fallback if the logo file isn't found
            st.markdown('<div style="color:white; font-size:1.5em; font-weight:bold;">zodopt</div>', unsafe_allow_html=True)

    with col2:
        st.markdown(
            f'<div class="header-banner">VISITOR REGISTRATION</div>',
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

def render_primary_details():
    """Renders the Name, Phone, and Email form fields (image_4de6d2.png)."""
    
    st.subheader("Primary Details")
    
    # Use a form to capture all data for this step
    with st.form("primary_details_form", clear_on_submit=False):
        # Full Name
        full_name = st.text_input("Name *", key="name_input", placeholder="Full Name", 
                                  value=st.session_state['visitor_data'].get('name', ''))

        # Phone Number (Split into Country Code and Number for visual consistency)
        col_code, col_number = st.columns([1, 4])
        with col_code:
            st.text_input("Country Code", value="+91", disabled=True, label_visibility="collapsed")
        with col_number:
            phone_number = st.text_input("Phone Number *", key="phone_input", placeholder="81234 56789", 
                                         value=st.session_state['visitor_data'].get('phone', ''), label_visibility="collapsed")

        # Email
        email = st.text_input("Email *", key="email_input", placeholder="your.email@example.com", 
                              value=st.session_state['visitor_data'].get('email', ''))

        # Submit/Next and Reset buttons
        col_reset, col_next = st.columns([4, 1])
        with col_reset:
            if st.form_submit_button("Reset", type="secondary"):
                 # Simple reset: clear current inputs and session state data for this step
                 st.session_state['visitor_data'].update({'name': '', 'phone': '', 'email': ''})
                 st.rerun() # Rerun to reflect the cleared state

        with col_next:
            if st.form_submit_button("Next →", type="primary"):
                if not (full_name and phone_number and email):
                    st.error("Please fill in all required fields (*).")
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

def render_secondary_details():
    """Renders the Other Details form fields (image_4de676.png)."""
    
    st.subheader("Other Details")

    # Use a form to capture all data for this step
    with st.form("secondary_details_form", clear_on_submit=False):
        
        # 1. Visit Type, From Company, Department, Designation
        st.subheader("Company Details")
        st.selectbox("Visit Type", ["-Select-", "Business", "Personal", "Other"], key='visit_type',
                     index=0 if st.session_state['visitor_data'].get('visit_type') is None else st.session_state['visitor_data'].get('visit_type'))
        
        st.text_input("From Company", key='from_company', 
                      value=st.session_state['visitor_data'].get('from_company', ''))
        
        st.selectbox("Department", ["-Select-", "Sales", "IT", "HR"], key='department',
                     index=0 if st.session_state['visitor_data'].get('department') is None else st.session_state['visitor_data'].get('department'))
        
        st.selectbox("Designation", ["-Select-", "Manager", "Engineer", "Director"], key='designation',
                     index=0 if st.session_state['visitor_data'].get('designation') is None else st.session_state['visitor_data'].get('designation'))
        
        # 2. Organization Address
        st.subheader("Organization Address")
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
                         index=0 if st.session_state['visitor_data'].get('country') is None else st.session_state['visitor_data'].get('country'))

        # 3. Gender, Purpose, Person to Meet
        st.subheader("Other Details")
        st.radio("Gender", ["Male", "Female", "Others"], horizontal=True, key='gender',
                 index=["Male", "Female", "Others"].index(st.session_state['visitor_data'].get('gender', 'Male')))
        
        st.selectbox("Purpose", ["-Select-", "Meeting", "Interview", "Delivery"], key='purpose',
                     index=0 if st.session_state['visitor_data'].get('purpose') is None else st.session_state['visitor_data'].get('purpose'))
        
        st.selectbox("Person to Meet", ["-Select-", "Alice", "Bob", "Charlie"], key='person_to_meet',
                     index=0 if st.session_state['visitor_data'].get('person_to_meet') is None else st.session_state['visitor_data'].get('person_to_meet'))
        
        # 4. Belongings (Checkboxes)
        st.subheader("Belongings")
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.checkbox("Bags", key='has_bags')
            st.checkbox("Electronic Items", key='has_electronic_items')
            st.checkbox("Charger", key='has_charger')
        with col_b2:
            st.checkbox("Documents", key='has_documents')
            st.checkbox("Laptop", key='has_laptop')
            st.checkbox("Power Bank", key='has_power_bank')

        st.markdown("---")
        
        # Previous and Next/Submit buttons (Red/Pink styling from the image)
        col_prev, col_next = st.columns(2)
        
        with col_prev:
            # Note: This button does not use st.form_submit_button 
            # as it needs to change the form state without validating/submitting the current form data
            if st.button("Previous", key='prev_button', use_container_width=True, 
                         # Apply custom styling to match the pink button color
                         help="Go back to Primary Details"):
                st.session_state['registration_step'] = 'primary'
                st.rerun()

        with col_next:
            if st.form_submit_button("Next", type="primary", use_container_width=True, help="Complete Registration"):
                # Save ALL data from session state keys used in this form
                # Note: For simplicity, we assume form validation has passed, but in a real app,
                # you'd validate required fields here.
                
                # Update session_state['visitor_data'] with current form values
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
                st.success("🎉 Visitor Registration Complete!")
                st.session_state['registration_step'] = 'complete'
                st.rerun() # Rerun to show the 'complete' state

# --- Main Application Logic ---

def main():
    """Main function to run the multi-step form."""
    
    # Render the header based on the current step
    render_header(st.session_state['registration_step'])

    # Conditional rendering based on the current step
    if st.session_state['registration_step'] == 'primary':
        render_primary_details()
    
    elif st.session_state['registration_step'] == 'secondary':
        render_secondary_details()

    elif st.session_state['registration_step'] == 'complete':
        st.subheader("Registration Summary")
        st.json(st.session_state['visitor_data'])
        
        st.markdown("---")
        if st.button("Start New Registration"):
            st.session_state['registration_step'] = 'primary'
            st.session_state['visitor_data'] = {} # Clear data for new start
            st.rerun()

if __name__ == "__main__":
    main()
