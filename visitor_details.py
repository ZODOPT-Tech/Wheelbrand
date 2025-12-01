import streamlit as st
from datetime import datetime
import json
import boto3
from botocore.exceptions import ClientError
import mysql.connector
from mysql.connector import Error

# ==============================================================================
# 1. CONFIGURATION & CREDENTIALS (AWS Integration)
# ==============================================================================

# Constants for AWS and DB
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
DEFAULT_DB_PORT = 3306

@st.cache_resource(ttl=3600)
def get_db_credentials():
    """Retrieves database credentials ONLY from AWS Secrets Manager."""
    st.info("Attempting to retrieve DB credentials from AWS Secrets Manager...")
    try:
        # Use an explicit client for Secrets Manager
        client = boto3.client('secretsmanager', region_name=AWS_REGION)
        
        get_secret_value_response = client.get_secret_value(
            SecretId=AWS_SECRET_NAME
        )
        
        if 'SecretString' not in get_secret_value_response:
            raise ValueError("SecretString is missing in the AWS response.")
            
        secret = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret)
        
        required_keys = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        if not all(key in secret_dict for key in required_keys):
            raise KeyError("Missing required DB keys (DB_HOST, DB_NAME, etc.) in the AWS secret.")

        st.success("DB credentials successfully retrieved.")
        return {
            "DB_HOST": secret_dict["DB_HOST"],
            "DB_NAME": secret_dict["DB_NAME"],
            "DB_USER": secret_dict["DB_USER"],
            "DB_PASSWORD": secret_dict["DB_PASSWORD"],
        }
        
    except ClientError as e:
        error_msg = f"AWS Secrets Manager API Error ({e.response['Error']['Code']}): Check IAM Role and ARN."
        st.error(error_msg)
        raise EnvironmentError(error_msg)
    except Exception as e:
        error_msg = f"FATAL: Credential Retrieval Failure: {e}"
        st.error(error_msg)
        raise EnvironmentError(error_msg)

@st.cache_resource(ttl=None)
def get_fast_connection():
    """Returns a persistent MySQL connection object, halting the app on failure."""
    try:
        credentials = get_db_credentials()
        
        conn = mysql.connector.connect(
            host=credentials["DB_HOST"],
            user=credentials["DB_USER"],
            password=credentials["DB_PASSWORD"],
            database=credentials["DB_NAME"],
            port=DEFAULT_DB_PORT,
            autocommit=True, # For immediate persistence of changes
            connection_timeout=10,
        )
        st.success("MySQL connection established successfully.")
        return conn
    except EnvironmentError:
        st.stop()
    except Error as err:
        error_msg = f"FATAL: MySQL Connection Error: Cannot connect. Details: {err.msg}"
        st.error(error_msg)
        st.stop()
    except Exception as e:
        error_msg = f"FATAL: Unexpected Connection Error: {e}"
        st.error(error_msg)
        st.stop()


# ==============================================================================
# 2. CONFIGURATION & STATE SETUP
# ==============================================================================

def initialize_session_state():
    """Initializes all necessary session state variables if they do not exist."""
    
    # Registration flow state
    if 'registration_step' not in st.session_state:
        st.session_state['registration_step'] = 'primary'
    if 'visitor_data' not in st.session_state:
        # visitor_data stores validated primary data
        st.session_state['visitor_data'] = {}
    
    # Global state (assumed to be set by a previous login screen)
    if 'company_id' not in st.session_state:
        st.session_state['company_id'] = None
    if 'admin_logged_in' not in st.session_state:
        st.session_state['admin_logged_in'] = False

def navigate_to_main_screen():
    """Clears registration specific state and redirects to the main entry point."""
    
    # 1. Clear ALL session state related to the current registration flow
    keys_to_clear = [
        'registration_step', 'visitor_data'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # 2. Set the main navigation key (Assuming 'main_screen' is the target home page)
    st.session_state['current_page'] = 'main_screen'
    st.rerun()

# ==============================================================================
# 3. DATABASE INTERACTION & SERVICE
# ==============================================================================

def save_visitor_data_to_db(data):
    """Saves the complete visitor registration data to the MySQL database."""
    
    conn = get_fast_connection()
    if conn is None:
        return False
    
    cursor = None
    success = False
    
    # Map state keys to DB column names (using data for clarity)
    fields = (
        "company_id", "registration_timestamp", "full_name", "phone_number", "email", 
        "visit_type", "from_company", "department", "designation", "address_line_1", 
        "city", "state", "postal_code", "country", "gender", "purpose", 
        "person_to_meet", "has_bags", "has_documents", "has_electronic_items", 
        "has_laptop", "has_charger", "has_power_bank"
    )
    
    values = (
        st.session_state.get('company_id'),
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
    
    placeholders = ", ".join(["%s"] * len(fields))
    columns = ", ".join(fields)
    sql = f"INSERT INTO visitors ({columns}) VALUES ({placeholders})"
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql, values)
        conn.commit()
        success = True
    except Error as e:
        st.error(f"Database Insertion Error: Failed to save registration data. Details: {e}")
        conn.rollback()
    except Exception as e:
        st.error(f"An unexpected error occurred during database save: {e}")
    finally:
        if cursor:
            cursor.close()
    
    return success

# ==============================================================================
# 4. HELPER FUNCTIONS (CSS and Header)
# ==============================================================================

def render_custom_styles():
    """Applies custom CSS for the header banner and buttons."""
    logo_svg_data = """
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L2 22H22L12 2Z" fill="#FFFFFF"/>
        <path d="M12 7L16 15H8L12 7Z" fill="#5d28a5"/>
    </svg>
    """

    st.markdown(
        f"""
        <style>
        /* General layout and font */
        .stApp {{
            font-family: 'Inter', sans-serif;
        }}
        
        /* Header Banner Styling */
        .header-banner {{
            background-color: #5d28a5; /* Deep Purple */
            color: white;
            padding: 15px 20px;
            font-size: 1.8em;
            font-weight: 700;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .zodopt-tag {{
            display: flex;
            align-items: center;
            font-size: 0.6em;
            font-weight: 400;
            gap: 5px;
        }}
        
        /* Step Navigation Tabs */
        .step-tabs {{
            display: flex;
            margin-bottom: 25px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .step-tab {{
            padding: 10px 20px;
            cursor: default;
            font-weight: 600;
            color: #888;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
        }}
        .step-tab.active {{
            color: #5d28a5;
            border-bottom: 3px solid #5d28a5;
        }}
        
        /* Streamlit Button Overrides */
        /* Style for the "Next" / "Submit" button (Red/Pink/Accent) */
        div.stFormSubmitButton > button {{
            background-color: #ff545d; /* Pink/Red Accent */
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
            transition: background-color 0.2s;
        }}
        div.stFormSubmitButton > button:hover {{
            background-color: #e54c52;
        }}
        
        /* Style for all standard st.button (Previous/Reset) */
        div.stButton > button {{ 
            background-color: #f0f0f0;
            color: #555;
            border: 1px solid #ccc;
            padding: 10px 20px;
            border-radius: 8px;
            transition: background-color 0.2s;
        }}
        div.stButton > button:hover {{
            background-color: #e5e5e5;
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
                zodopt
                {logo_svg}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown(
        f"""
        <div class="step-tabs">
            <div class="step-tab {'active' if current_step == 'primary' else ''}">1. PRIMARY DETAILS</div>
            <div class="step-tab {'active' if current_step == 'secondary' else ''}">2. SECONDARY DETAILS</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==============================================================================
# 5. STEP 1: Primary Details Form
# ==============================================================================

def render_primary_details_form():
    """Renders the Name, Phone, and Email form fields."""
    
    # 1. Navigation Buttons (Outside the form)
    col_reset, col_spacer = st.columns([1, 3])
    with col_reset:
        if st.button("Reset / Main Menu", use_container_width=True, key="reset_primary"):
            navigate_to_main_screen()

    # Placeholders for error messages
    error_placeholder = st.empty()

    with st.form("primary_details_form", clear_on_submit=False):
        st.markdown("### Visitor Contact Information")
        
        # Initial values from session state
        initial_name = st.session_state['visitor_data'].get('name', '')
        initial_phone = st.session_state['visitor_data'].get('phone', '')
        initial_email = st.session_state['visitor_data'].get('email', '')

        # 1. Full Name
        st.write("Full Name *")
        full_name = st.text_input("Name", key="form_name", placeholder="Full Name (As per ID)", 
                                  value=initial_name, label_visibility="collapsed")

        # 2. Phone Number
        st.write("Phone Number *")
        col_code, col_number = st.columns([0.5, 3.5])
        with col_code:
            st.text_input("Country Code", value="+91", disabled=True, label_visibility="collapsed", key="country_code_display")
        with col_number:
            phone_number = st.text_input("Phone Number", key="form_phone", placeholder="81234 56789", 
                                         value=initial_phone, label_visibility="collapsed")

        # 3. Email
        st.write("Email Address *")
        email = st.text_input("Email", key="form_email", placeholder="your.email@example.com", 
                              value=initial_email, label_visibility="collapsed")

        # Submit/Next Button Container (INSIDE the form)
        col_spacer_submit, col_next = st.columns([3, 1])
        with col_next:
            submitted = st.form_submit_button("Next →", use_container_width=True)

        # --- Logic check for Submission (Next) ---
        if submitted:
            # Simple validation check
            if not (full_name and phone_number and email):
                error_placeholder.error("⚠️ Please fill in all required fields (*).")
            # Basic phone validation (can be enhanced with regex)
            elif not phone_number.isdigit() or len(phone_number) < 10:
                error_placeholder.error("⚠️ Please enter a valid 10-digit phone number.")
            else:
                # Save validated data to session state for step 2
                st.session_state['visitor_data'].update({
                    'name': full_name,
                    'phone': phone_number,
                    'email': email
                })
                # Navigate to next step
                st.session_state['registration_step'] = 'secondary'
                st.rerun()

# ==============================================================================
# 6. STEP 2: Secondary Details Form
# ==============================================================================

def render_secondary_details_form():
    """Renders the Other Details form fields and handles final submission to DB."""
    
    # Placeholders for error/success messages
    message_placeholder = st.empty()
    
    # --- PREVIOUS / MAIN MENU BUTTONS (OUTSIDE the form) ---
    col_prev, col_main_menu, col_end_spacer = st.columns([1, 1, 2])
    with col_prev:
        if st.button("← Previous Step", key='prev_button_secondary', use_container_width=True):
            st.session_state['registration_step'] = 'primary'
            st.rerun()

    with col_main_menu:
        if st.button("Back to Main Menu", key='main_menu_button_secondary', use_container_width=True):
            navigate_to_main_screen()
            
    st.markdown("---") # Visual separator

    # Helper to get current value from session state
    def get_val(key, default=''):
        return st.session_state['visitor_data'].get(key, default)
        
    # Default selection for radio
    gender_options = ["Male", "Female", "Others"]
    default_gender_index = gender_options.index(get_val('gender', 'Male'))
        
    with st.form("secondary_details_form", clear_on_submit=False):
        st.markdown("### Organizational & Visit Details")
        
        # 1. Visit Details
        col_vt, col_fc = st.columns(2)
        with col_vt:
            visit_type = st.text_input("Visit Type", key='form_visit_type', 
                                     value=get_val('visit_type'), 
                                     placeholder="e.g., Business, Personal")
        with col_fc:
            from_company = st.text_input("From Company", key='form_from_company', 
                                       value=get_val('from_company'))
        
        # 2. Professional Details
        col_dept, col_des = st.columns(2)
        with col_dept:
            department = st.text_input("Department", key='form_department',
                                     value=get_val('department'),
                                     placeholder="e.g., Sales, HR, IT")
        with col_des:
            designation = st.text_input("Designation", key='form_designation',
                                      value=get_val('designation'),
                                      placeholder="e.g., Manager, Engineer")
        
        # 3. Address
        st.text_input("Organization Address", placeholder="Address Line 1", key='form_address_line_1',
                      value=get_val('address_line_1'))
        
        col_city, col_state = st.columns(2)
        with col_city:
            city = st.text_input("City / District", key='form_city',
                                 value=get_val('city'))
        with col_state:
            state = st.text_input("State / Province", key='form_state',
                                  value=get_val('state'))
                
        col_postal, col_country = st.columns(2)
        with col_postal:
            postal_code = st.text_input("Postal Code", key='form_postal_code',
                                      value=get_val('postal_code'))
        with col_country:
            country = st.text_input("Country", key='form_country',
                                  value=get_val('country'),
                                  placeholder="e.g., India, USA")

        st.markdown("---")
        
        # 4. Meeting and Personal Details
        gender = st.radio("Gender", gender_options, horizontal=True, key='form_gender',
                          index=default_gender_index, help="Select your gender.")
        
        col_purpose, col_person = st.columns(2)
        with col_purpose:
            purpose = st.text_input("Purpose of Visit", key='form_purpose',
                                  value=get_val('purpose'),
                                  placeholder="e.g., Meeting, Interview")
        with col_person:
            person_to_meet = st.text_input("Person to Meet *", key='form_person_to_meet',
                                         value=get_val('person_to_meet'),
                                         placeholder="e.g., Alice, Bob")
        
        st.markdown("#### Belongings Declaration")
        # 5. Belongings (using explicit keys for form values)
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            bags = st.checkbox("Bags", key='form_has_bags', value=get_val('has_bags', False))
            electronics = st.checkbox("Electronic Items", key='form_has_electronic_items', value=get_val('has_electronic_items', False))
            charger = st.checkbox("Charger", key='form_has_charger', value=get_val('has_charger', False))
        with col_b2:
            documents = st.checkbox("Documents", key='form_has_documents', value=get_val('has_documents', False))
            laptop = st.checkbox("Laptop", key='form_has_laptop', value=get_val('has_laptop', False))
            power_bank = st.checkbox("Power Bank", key='form_has_power_bank', value=get_val('has_power_bank', False))

        st.markdown("---")
        
        # --- SUBMISSION BUTTON (INSIDE the form) ---
        col_spacer_submit, col_submit = st.columns([3, 1])
        
        with col_submit:
            submitted = st.form_submit_button("Complete Registration →", use_container_width=True)

        # --- Submission Logic ---
        if submitted:
            # Mandatory check
            if not person_to_meet:
                message_placeholder.error("⚠️ 'Person to Meet' is a required field.")
                return

            # Consolidate all form data into the final dictionary
            final_data = st.session_state['visitor_data']
            final_data.update({
                'visit_type': visit_type,
                'from_company': from_company,
                'department': department,
                'designation': designation,
                'address_line_1': address_line_1,
                'city': city,
                'state': state,
                'postal_code': postal_code,
                'country': country,
                'gender': gender,
                'purpose': purpose,
                'person_to_meet': person_to_meet,
                # Belongings are captured directly from checkboxes (True/False)
                'has_bags': bags,
                'has_documents': documents,
                'has_electronic_items': electronics,
                'has_laptop': laptop,
                'has_charger': charger,
                'has_power_bank': power_bank
            })
            
            # Save to Database
            if save_visitor_data_to_db(final_data):
                message_placeholder.success("🎉 Visitor Registration Complete! You are now checked in.")
                st.balloons()
                
                # Clear session state for next registration
                st.session_state['registration_step'] = 'primary'
                st.session_state['visitor_data'] = {} 
                # Redirect to the main admin dashboard for visitor view
                st.session_state['current_page'] = 'visitor_dashboard'
            else:
                # Error already displayed in save_visitor_data_to_db
                message_placeholder.error("Registration failed due to a database error.")
            
            st.rerun()

# ==============================================================================
# 7. Main Application Logic
# ==============================================================================

def render_details_page():
    """Main function to run the multi-step visitor registration form."""
    
    # 1. Initialize State
    initialize_session_state()
    
    # 2. ENFORCE LOGIN CHECK
    if not st.session_state.get('admin_logged_in'):
        st.error("Access Denied: Please log in as an Admin to register visitors.")
        st.session_state['current_page'] = 'visitor_login' # Redirect to login page
        st.rerun()
        return
        
    if not st.session_state.get('company_id'):
        st.error("Session missing Company ID. Please log in again.")
        st.session_state['current_page'] = 'visitor_login'
        st.rerun()
        return
        
    # 3. Connection Test (Stops app if connection fails)
    # This call is placed here to ensure connection is ready before rendering forms
    conn = get_fast_connection()
    if conn is None:
        return # App should already be stopped by get_fast_connection

    # 4. Render Header and Navigation
    render_header(st.session_state['registration_step'])

    # 5. Render Forms based on Step
    if st.session_state['registration_step'] == 'primary':
        render_primary_details_form()
    
    elif st.session_state['registration_step'] == 'secondary':
        render_secondary_details_form()
    

if __name__ == "__main__":
    # --- Mock login state for direct file testing (Remove in production environment) ---
    if 'admin_logged_in' not in st.session_state:
        st.session_state['admin_logged_in'] = True
        st.session_state['company_id'] = 1 
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'visitor_details'
        
    render_details_page()
