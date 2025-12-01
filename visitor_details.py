import streamlit as st
import base64
from pathlib import Path
import mysql.connector
from datetime import datetime
from mysql.connector import Error

# Placeholder path
LOGO_PATH = "zodopt.png"  

# --- CONFIGURATION & STATE SETUP FUNCTION (FIXED) ---

def initialize_session_state():
    """Initializes all necessary session state variables if they do not exist."""
    if 'registration_step' not in st.session_state:
        st.session_state['registration_step'] = 'primary'
    if 'visitor_data' not in st.session_state:
        st.session_state['visitor_data'] = {}
    # Ensure company_id exists (it is set by visitor_login.py)
    if 'company_id' not in st.session_state:
        st.session_state['company_id'] = 1

# --- DATABASE CONNECTION & SERVICE ---

def get_db_connection():
    """Establishes a connection to the MySQL database using Streamlit secrets."""
    try:
        # NOTE: This relies on st.secrets being configured with mysql_db credentials
        conn = mysql.connector.connect(
            host=st.secrets["mysql_db"]["host"],
            database=st.secrets["mysql_db"]["database"],
            user=st.secrets["mysql_db"]["user"],
            password=st.secrets["mysql_db"]["password"]
        )
        return conn
    except Error as e:
        st.error(f"Database Connection Error: Could not connect to MySQL. Details: {e}")
        return None

def save_visitor_data_to_db(data):
    """Saves the complete visitor registration data to the MySQL database."""
    conn = get_db_connection()
    if conn is None:
        return False
    
    cursor = conn.cursor()
    
    # List of fields in the 'visitors' table (must match the order of 'values')
    fields = (
        "company_id", "registration_timestamp", "full_name", "phone_number", "email", 
        "visit_type", "from_company", "department", "designation", "address_line_1", 
        "city", "state", "postal_code", "country", "gender", "purpose", 
        "person_to_meet", "has_bags", "has_documents", "has_electronic_items", 
        "has_laptop", "has_charger", "has_power_bank"
    )
    
    # Collect values in the exact order of fields
    values = (
        st.session_state['company_id'],
        datetime.now(),
        data.get('name'), 
        data.get('phone'), 
        data.get('email'), 
        data.get('visit_type'), 
        data.get('from_company'), 
        data.get('department'), 
        data.get('designation'), 
        data.get('address_line_1'), 
        data.get('city'), 
        data.get('state'), 
        data.get('postal_code'), 
        data.get('country'), 
        data.get('gender'), 
        data.get('purpose'), 
        data.get('person_to_meet'), 
        data.get('has_bags', False), 
        data.get('has_documents', False), 
        data.get('has_electronic_items', False), 
        data.get('has_laptop', False), 
        data.get('has_charger', False), 
        data.get('has_power_bank', False)
    )
    
    # Construct the SQL INSERT statement
    placeholders = ", ".join(["%s"] * len(fields))
    columns = ", ".join(fields)
    sql = f"INSERT INTO visitors ({columns}) VALUES ({placeholders})"
    
    try:
        cursor.execute(sql, values)
        conn.commit()
        return True
    except Error as e:
        st.error(f"Database Insertion Error: Failed to save registration data. Details: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


# --- HELPER FUNCTIONS (CSS and Header) ---

def img_to_base64(img_path):
    """Converts an image file to a base64 string for CSS embedding."""
    return None 

def render_custom_styles():
    """Applies custom CSS for the header banner and buttons."""
    logo_svg_data = """
    <div class="zodopt-logo-container">
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L2 22H22L12 2Z" fill="#FFFFFF"/>
        <path d="M12 7L16 15H8L12 7Z" fill="#5d28a5"/>
    </svg>
    </div>
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
        .zodopt-logo-container {{
            width: 40px; 
            height: 40px; 
            margin-left: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
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
    return logo_svg_data

def render_header(current_step):
    """Renders the header with the logo and step navigation."""
    logo_svg = render_custom_styles()
    st.markdown(
        f"""
        <div class="header-banner">
            VISITOR REGISTRATION
            <div class="zodopt-tag">
                {logo_svg}
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
            st.markdown("### Primary Details")
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
                    # Basic validation
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

# --- Step 2: Secondary Details Form ---

def render_secondary_details_form():
    """Renders the Other Details form fields and handles final submission to DB."""
    
    with st.container(border=False):
        st.markdown("### Other Details")

        # Define the button columns OUTSIDE the form (to handle navigation before form submission)
        col_prev, col_next_container = st.columns(2)
        
        with col_prev:
            if st.button("Previous", key='prev_button_secondary', use_container_width=True):
                st.session_state['registration_step'] = 'primary'
                st.rerun()

        # The rest of the form fields and the submit button go inside st.form
        with st.form("secondary_details_form", clear_on_submit=False):
            
            # --- FORM FIELDS ---
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
                      index=["Male", "Female", "Others"].index(st.session_state['visitor_data'].get('gender', 'Male')),
                      help="Select your gender.")
            
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
                if st.form_submit_button("Complete Registration →", use_container_width=True):
                    
                    # 1. Update session_state['visitor_data'] with all current form values
                    final_data = st.session_state['visitor_data']
                    final_data.update({
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
                    
                    # 2. Save data to database
                    if save_visitor_data_to_db(final_data):
                        st.balloons()
                        st.success("🎉 Visitor Registration Complete! Details have been recorded. Redirecting to Dashboard...")
                        
                        # Clear registration state and REDIRECT TO DASHBOARD
                        st.session_state['registration_step'] = 'primary'
                        st.session_state['visitor_data'] = {} 
                        st.session_state['current_page'] = 'visitor_dashboard' 
                        st.rerun() 
                    
                    # Rerunning even on failure to clear form submission state/update messages
                    st.rerun() 

# --- Main Application Logic ---

def render_details_page():
    """Main function to run the multi-step visitor registration form."""
    
    # 1. ENFORCE LOGIN CHECK
    if not st.session_state.get('admin_logged_in'):
        st.error("Access Denied: Please log in as an Admin to register visitors.")
        st.session_state['current_page'] = 'visitor_login'
        st.rerun()
        return
        
    # 2. Initialize session state at the entry point to prevent KeyError
    initialize_session_state() 
    
    render_header(st.session_state['registration_step'])

    if st.session_state['registration_step'] == 'primary':
        render_primary_details_form()
    
    elif st.session_state['registration_step'] == 'secondary':
        render_secondary_details_form()
    
    # The 'complete' block is removed as the app now redirects to the dashboard directly.

if __name__ == "__main__":
    render_details_page()
