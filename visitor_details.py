import streamlit as st


# --- Session State Management ---
# Initialize session state keys for navigation and form data persistence
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = 'primary'
    
if 'name' not in st.session_state:
    st.session_state['name'] = ""
if 'phone' not in st.session_state:
    st.session_state['phone'] = ""
if 'email' not in st.session_state:
    st.session_state['email'] = ""
# Initialize other secondary fields to prevent key errors
if 'visit_type' not in st.session_state: st.session_state['visit_type'] = ""
if 'from_company' not in st.session_state: st.session_state['from_company'] = ""
if 'gender' not in st.session_state: st.session_state['gender'] = "Male"


# --- Utility Function for Header with Logo (Refined to match banner image) ---
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
                font-weight: 800; /* Extra bold for primary text */
                letter-spacing: 1px;
                margin: 0;
            }
            .zodopt-logo-text {
                font-family: 'Poppins', sans-serif;
                font-size: 24px;
                font-weight: 600; /* Semi-bold for logo text */
                letter-spacing: 0.5px;
            }
            .zodopt-logo-red { color: #FF4B4B; } /* Red part of zodopt */
            .zodopt-logo-blue { color: #4059A1; } /* Blue part of zodopt (approximate match) */
            
            /* Overriding Streamlit's default header margin */
            .stApp > header { display: none; }
            
            /* Styles for step navigation */
            .step-container {
                display: flex;
                margin-bottom: 20px;
                border-bottom: 3px solid #E0E0E0; /* Light gray line under tabs */
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
        <div class="zodopt-header">
            <h1 class="zodopt-title-text">VISITOR REGISTRATION</h1>
            <div class="zodopt-logo-text">
                <span class="zodopt-logo-red">zo</span><span class="zodopt-logo-blue">dopt</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- Step Functions ---

def render_primary_details():
    """Renders the Primary Details form (Name, Phone, Email)."""
    render_header()
    
    # Custom HTML for the tab-like navigation
    st.markdown("""
    <div class="step-container">
        <div class="step active-step">PRIMARY DETAILS</div>
        <div class="step" style="color: #9E9E9E;">SECONDARY DETAILS</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("primary_form"):
        # Based on image_4e6d9f.png
        # Use initial value from session state to allow reset
        st.text_input("Name *", key="name", placeholder="Full Name", value=st.session_state.name)
        
        # Phone input simulation 
        col_code, col_number = st.columns([1, 4])
        with col_code:
            st.text_input("Phone * (Code)", value="+91", label_visibility="collapsed")
        with col_number:
            # Use initial value from session state to allow reset
            st.text_input("Phone * (Number)", key="phone", placeholder="81234 56789", label_visibility="collapsed", value=st.session_state.phone)
        
        # Use initial value from session state to allow reset
        st.text_input("Email *", key="email", placeholder="your.email@example.com", value=st.session_state.email)

        st.markdown("---")
        
        col_reset, col_next = st.columns(2)
        
        # Reset button (FIXED: now uses st.form_submit_button inside the form)
        with col_reset:
            if st.form_submit_button("Reset", key="reset_primary_submit", use_container_width=True, type="secondary"):
                # Clear inputs by resetting session state keys and rerunning
                st.session_state.name = ""
                st.session_state.phone = ""
                st.session_state.email = ""
                st.rerun()

        # Button to proceed
        with col_next:
            if st.form_submit_button("Next →", key="next_primary_submit", use_container_width=True, type="primary"):
                # Basic validation
                if st.session_state.name and st.session_state.phone and st.session_state.email:
                    st.session_state['current_step'] = 'secondary'
                    st.rerun()
                else:
                    st.error("Please fill in all mandatory fields (*).")


def render_secondary_details():
    """Renders the Secondary Details form (Company info, Gender, Purpose, Belongings)."""
    render_header()

    # Custom HTML for the tab-like navigation (Secondary is active)
    st.markdown("""
    <div class="step-container">
        <div class="step" style="color: #9E9E9E;">PRIMARY DETAILS</div>
        <div class="step active-step">SECONDARY DETAILS</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Based on image_4e6ddb.png
    with st.form("secondary_form"):
        st.subheader("🏢 Organizational Details")
        st.text_input("Visit Type", key="visit_type", placeholder="e.g., Business, Personal", value=st.session_state.visit_type)
        st.text_input("From Company", key="from_company", placeholder="e.g., Tech Solutions Inc.", value=st.session_state.from_company)
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
        st.radio("Gender", options=["Male", "Female", "Others"], horizontal=True, key="gender", index=["Male", "Female", "Others"].index(st.session_state.gender))

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
            if st.form_submit_button("Previous", key="prev_secondary_submit", use_container_width=True, type="secondary"):
                # Save current state before navigating back
                st.session_state['current_step'] = 'primary'
                st.rerun()

        with col_next:
            # Final submission button
            if st.form_submit_button("Submit", key="submit_secondary_submit", use_container_width=True, type="primary"):
                # Retrieve all collected data
                visitor_data = {key: st.session_state.get(key) for key in st.session_state if key not in ['current_step', 'visitor_data']}
                
                # Display success and confirmation
                st.success("Visitor Registration Complete! Thank you.")
                st.balloons()
                
                # Update state for completion page
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
    
    if st.button("Start New Registration", key="start_new_reg"):
        st.session_state['current_step'] = 'primary'
        # Clear specific session state keys to reset form data
        keys_to_clear = [key for key in st.session_state if key not in ['current_step']]
        for key in keys_to_clear:
            del st.session_state[key]
        st.rerun()


# --- Main Application Logic ---
if st.session_state['current_step'] == 'primary':
    render_primary_details()
elif st.session_state['current_step'] == 'secondary':
    render_secondary_details()
elif st.session_state['current_step'] == 'complete':
    render_complete_page()
