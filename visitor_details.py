import streamlit as st

# --- Session State Management ---
# Initialize session state for multi-page/multi-step navigation
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = 'primary'

# --- Logo Path (Assuming 'zodopt.png' is in the same directory) ---
LOGO_PATH = "zodopt.png"

# --- Utility Function for Header with Logo ---
def render_header():
    """Renders the custom header with a logo on the right."""
    # Use columns to align the title and the logo
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(
            """
            <div style='padding-top: 10px; padding-bottom: 5px;'>
                <h1 style='color: #4A148C; font-size: 32px;'>Visitor Registration</h1>
                <p style='color: #90A4AE; font-size: 16px;'>Please fill in your details</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        try:
            # Display the logo if it exists
            st.image(LOGO_PATH, width=100)
        except FileNotFoundError:
            # Fallback if the logo file isn't found
            st.warning("Logo file 'zodopt.png' not found.")

    st.markdown("---") # Separator after the header

# --- Step Functions ---

def render_primary_details():
    """Renders the Primary Details form (Name, Phone, Email)."""
    render_header()
    
    # Custom CSS for the tab-like navigation (Primary is active)
    st.markdown("""
    <style>
        .step-container {
            display: flex;
            margin-bottom: 20px;
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
            color: #4A148C; /* Purple for active tab text */
            border-bottom: 3px solid #4A148C !important; /* Purple line for active tab */
        }
    </style>
    <div class="step-container">
        <div class="step active-step">PRIMARY DETAILS</div>
        <div class="step" style="border-bottom: 3px solid #E0E0E0; color: #9E9E9E;">SECONDARY DETAILS</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("primary_form"):
        # Based on image_4e6d9f.png
        st.text_input("Name *", key="name", placeholder="Full Name")
        
        # Phone input simulation (Streamlit doesn't natively support splitting the country code)
        col_code, col_number = st.columns([1, 4])
        with col_code:
            st.text_input("Phone * (Code)", value="+91", label_visibility="collapsed")
        with col_number:
            st.text_input("Phone * (Number)", key="phone", placeholder="81234 56789", label_visibility="collapsed")
        
        st.text_input("Email *", key="email", placeholder="your.email@example.com")

        st.markdown("---")
        
        # Button to proceed
        if st.form_submit_button("Next →", use_container_width=True, type="primary"):
            # Basic validation
            if st.session_state.name and st.session_state.phone and st.session_state.email:
                st.session_state['current_step'] = 'secondary'
                st.rerun()
            else:
                st.error("Please fill in all mandatory fields (*).")
                
        # Reset button
        if st.button("Reset", key="reset_primary"):
            # Clear inputs (will refresh the form)
            st.session_state.name = ""
            st.session_state.phone = ""
            st.session_state.email = ""
            st.rerun()


def render_secondary_details():
    """Renders the Secondary Details form (Company info, Gender, Purpose, Belongings)."""
    render_header()

    # Custom CSS for the tab-like navigation (Secondary is active)
    st.markdown("""
    <style>
        .step-container {
            display: flex;
            margin-bottom: 20px;
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
            color: #4A148C; /* Purple for active tab text */
            border-bottom: 3px solid #4A148C !important; /* Purple line for active tab */
        }
    </style>
    <div class="step-container">
        <div class="step" style="border-bottom: 3px solid #E0E0E0; color: #9E9E9E;">PRIMARY DETAILS</div>
        <div class="step active-step">SECONDARY DETAILS</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Based on image_4e6ddb.png
    with st.form("secondary_form"):
        st.subheader("🏢 Organizational Details")
        st.text_input("Visit Type", key="visit_type", placeholder="e.g., Business, Personal")
        st.text_input("From Company", key="from_company", placeholder="e.g., Tech Solutions Inc.")
        st.text_input("Department", key="department", placeholder="e.g., Sales, HR, Engineering")
        st.text_input("Designation", key="designation", placeholder="e.g., Manager, Developer")

        st.markdown("---")

        st.subheader("📍 Organization Address")
        st.text_input("Address Line 1", key="addr1")
        
        col_city, col_state = st.columns(2)
        with col_city:
            st.text_input("City / District", key="city")
        with col_state:
            st.text_input("State / Province", key="state")
            
        col_postal, col_country = st.columns(2)
        with col_postal:
            st.text_input("Postal Code", key="postal_code")
        with col_country:
            st.text_input("Country", key="country")

        st.markdown("---")

        st.subheader("🧑‍🤝‍👩 Other Details")
        
        # Gender (Radio button simulation)
        st.radio("Gender", options=["Male", "Female", "Others"], horizontal=True, key="gender")

        # Purpose (Input field instead of dropdown)
        st.text_input("Purpose", key="purpose", placeholder="e.g., Meeting, Delivery, Interview")
        
        st.text_input("Person to Meet", key="person_to_meet", placeholder="Full Name of Contact Person")

        st.markdown("---")
        
        st.subheader("💼 Belongings Check")
        # Belongings (Checkbox simulation)
        col_bags, col_docs, col_elect, col_laptop, col_charge, col_power = st.columns(6)
        with col_bags:
            st.checkbox("Bags", key="bags")
        with col_docs:
            st.checkbox("Documents", key="documents")
        with col_elect:
            st.checkbox("Electronic Items", key="electronic")
        with col_laptop:
            st.checkbox("Laptop", key="laptop")
        with col_charge:
            st.checkbox("Charger", key="charger")
        with col_power:
            st.checkbox("Power Bank", key="power_bank")


        st.markdown("---")
        
        # Navigation Buttons
        col_prev, col_next = st.columns(2)
        
        with col_prev:
            if st.form_submit_button("Previous", use_container_width=True, type="secondary"):
                st.session_state['current_step'] = 'primary'
                st.rerun()

        with col_next:
            # Final submission button
            if st.form_submit_button("Submit", use_container_width=True, type="primary"):
                # Here you would typically process and save the data
                
                # Retrieve all collected data
                visitor_data = {
                    "Name": st.session_state.get('name'),
                    "Phone": st.session_state.get('phone'),
                    "Email": st.session_state.get('email'),
                    "Visit Type": st.session_state.get('visit_type'),
                    "Company": st.session_state.get('from_company'),
                    "Gender": st.session_state.get('gender'),
                    # ... add all other fields
                }
                
                # Display success and confirmation
                st.success("Visitor Registration Complete! Thank you.")
                st.balloons()
                # Optionally show the data collected
                st.session_state['current_step'] = 'complete'
                st.session_state['visitor_data'] = visitor_data
                st.rerun()


def render_complete_page():
    """Renders the completion page."""
    render_header()
    st.subheader("🎉 Registration Successful!")
    st.write("Your details have been submitted. Please wait for confirmation.")

    # Show a summary of the collected data
    st.subheader("Summary of Details")
    st.json(st.session_state.get('visitor_data', {}))
    
    if st.button("Start New Registration"):
        st.session_state['current_step'] = 'primary'
        # Clear specific session state keys to reset form data
        keys_to_clear = ['name', 'phone', 'email', 'visit_type', 'from_company', 'gender', 'visitor_data']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


# --- Main Application Logic ---
if st.session_state['current_step'] == 'primary':
    render_primary_details()
elif st.session_state['current_step'] == 'secondary':
    render_secondary_details()
elif st.session_state['current_step'] == 'complete':
    render_complete_page()
