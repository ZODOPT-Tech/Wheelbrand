import streamlit as st
import re
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
# NOTE: The ARN below is a mock value and must be replaced with the actual ARN in a real deployment.
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
DEFAULT_DB_PORT = 3306
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

@st.cache_resource(ttl=3600)
def get_db_credentials():
    """
    Retrieves database credentials ONLY from AWS Secrets Manager.
    The response is cached for 1 hour (3600 seconds).
    """
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
        
        try:
            secret_dict = json.loads(secret)
        except json.JSONDecodeError:
            raise ValueError("AWS secret content is not valid JSON.")

        required_keys = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        if not all(key in secret_dict for key in required_keys):
            missing_keys = [k for k in required_keys if k not in secret_dict]
            raise KeyError(f"Missing required DB keys in the AWS secret: {', '.join(missing_keys)}")

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
        error_msg = f"FATAL: Credential Retrieval Failure: {type(e).__name__} - {e}"
        st.error(error_msg)
        raise EnvironmentError(error_msg)

@st.cache_resource(ttl=None)
def get_fast_connection():
    """
    Returns a persistent MySQL connection object.
    Halts the application on initial connection failure.
    Includes a connection ping to ensure the cached connection is active.
    """
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
        # Verify and reconnect if necessary before returning the cached object
        conn.ping(reconnect=True)
        st.success("MySQL connection established successfully.")
        return conn
    except EnvironmentError:
        # This error is raised by get_db_credentials and already displayed
        st.stop()
    except Error as err:
        error_msg = f"FATAL: MySQL Connection Error: Cannot connect. Details: {err.msg}"
        st.error(error_msg)
        st.stop()
    except Exception as e:
        error_msg = f"FATAL: Unexpected Connection Error: {type(e).__name__} - {e}"
        st.error(error_msg)
        st.stop()


# ==============================================================================
# 2. CONFIGURATION & STATE SETUP
# ==============================================================================

def initialize_session_state():
    """Initializes all necessary session state variables if they do not exist."""
    
    # App Flow State: 'menu' (default dashboard) or 'registration' (form flow)
    if 'app_flow' not in st.session_state:
        st.session_state['app_flow'] = 'menu'
        
    # Registration flow state (only used when app_flow == 'registration')
    if 'registration_step' not in st.session_state:
        st.session_state['registration_step'] = 'primary'
    if 'visitor_data' not in st.session_state:
        # visitor_data stores validated primary data and accumulates secondary data
        st.session_state['visitor_data'] = {}
    
    # Global state (assumed to be set by a previous login screen)
    if 'company_id' not in st.session_state:
        # Default to None or a secure default like 0 if not set, but the main logic checks this.
        st.session_state['company_id'] = None
    if 'admin_logged_in' not in st.session_state:
        st.session_state['admin_logged_in'] = False


def navigate_to_main_screen():
    """Clears registration specific state and sets the flow back to the main menu."""
    
    # Set the flow back to the main menu
    st.session_state['app_flow'] = 'menu'
    
    # Clear ALL session state related to the current registration flow
    keys_to_clear = [
        'registration_step', 'visitor_data'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Rerunning will restart the script, allowing the external app to manage navigation
    st.rerun()

# ==============================================================================
# 3. DATABASE INTERACTION & SERVICE
# ==============================================================================

def save_visitor_data_to_db(data):
    """
    Saves the complete visitor registration data, tied to the current company_id, 
    to the MySQL database using parameterized queries for security.
    """
    
    conn = get_fast_connection()
    # Check connection health again (important for cached objects)
    try:
        conn.ping(reconnect=True)
    except Exception as e:
        st.error(f"Database connection failed during save operation: {e}")
        return False
        
    current_company_id = st.session_state.get('company_id')
    if not current_company_id:
        st.error("SECURITY ERROR: Cannot save visitor data. Company ID is missing.")
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
    
    # Ensure boolean values are saved correctly as MySQL requires 0 or 1
    def to_db_bool(val):
        return 1 if val else 0

    values = (
        current_company_id, # EXPLICITLY using the company ID
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
        to_db_bool(data.get('has_bags', False)), 
        to_db_bool(data.get('has_documents', False)), 
        to_db_bool(data.get('has_electronic_items', False)), 
        to_db_bool(data.get('has_laptop', False)), 
        to_db_bool(data.get('has_charger', False)), 
        to_db_bool(data.get('has_power_bank', False))
    )
    
    placeholders = ", ".join(["%s"] * len(fields))
    columns = ", ".join(fields)
    sql = f"INSERT INTO visitors ({columns}) VALUES ({placeholders})"
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql, values)
        # Autocommit=True handles the commit, but we keep it here for explicit flow assurance
        conn.commit()
        success = True
    except Error as e:
        st.error(f"Database Insertion Error (Company ID: {current_company_id}): Failed to save registration data. Details: {e}")
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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap');
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
        div.stFormSubmitButton > button, div.stFormSubmitButton > button:focus:not(:active) {{
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
        
        /* Style for all standard st.button (Previous/Reset/Main Menu) */
        div.stButton > button, div.stButton > button:focus:not(:active) {{ 
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
        
        /* Style for the main action button (Start Registration) */
        #start_registration {{
            background-color: #5d28a5; /* Deep Purple */
            color: white;
            font-size: 1.2em;
            height: auto;
            padding: 20px 30px;
            border: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        #start_registration:hover {{
            background-color: #4b2085;
        }}
        </style>
        """, 
        unsafe_allow_html=True
    )
    return logo_svg_data

def render_app_header():
    """Renders the simplified main application header banner."""
    logo_svg = render_custom_styles()
    company_id = st.session_state.get('company_id', 'N/A')
    
    st.markdown(
        f"""
        <div class="header-banner">
            VISITOR MANAGEMENT SYSTEM (Company ID: {company_id})
            <div class="zodopt-tag">
                zodopt
                {logo_svg}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
def render_step_navigation(current_step):
    """Renders the step navigation tabs only during the registration flow."""
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
# 5. ADMIN MAIN SCREEN
# ==============================================================================

def render_admin_main_screen():
    """Renders the main menu/dashboard for the logged-in admin."""
    
    st.title("Admin Dashboard")
    st.subheader(f"Manage Visitor Operations for Facility")
    st.markdown("---")
    
    st.markdown("## Visitor Management Actions")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        # NOTE: Using a custom ID to apply specific button styling from CSS
        if st.button("Register New Visitor", key="start_registration", use_container_width=True):
            # Reset registration-specific state and start the flow
            st.session_state['registration_step'] = 'primary'
            st.session_state['visitor_data'] = {}
            st.session_state['app_flow'] = 'registration'
            st.rerun()

    with col2:
        # Placeholder for future functionality
        st.button("View Visitor Logs (WIP)", key="view_logs", use_container_width=True, disabled=True)
    
    st.markdown("""
        <div style="margin-top: 50px; padding: 20px; border: 1px dashed #5d28a5; border-radius: 8px; background-color: #f7f3ff;">
        <p style="font-size: 1.1em; font-weight: 600; color: #5d28a5;">
        Ready for Check-In
        </p>
        <p style="font-size: 0.9em; color: #777;">
        Click the **Register New Visitor** button to begin the quick, two-step registration process.
        </p>
        </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# 6. STEP 1: Primary Details Form
# ==============================================================================

def render_primary_details_form():
    """Renders the Name, Phone, and Email form fields with validation."""
    
    # 1. Navigation Buttons (Outside the form)
    col_reset, col_spacer = st.columns([1, 3])
    with col_reset:
        if st.button("Back to Main Menu", use_container_width=True, key="reset_primary"):
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
        st.write("Phone Number (10 digits) *")
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
            is_valid = True
            
            if not (full_name and phone_number and email):
                error_placeholder.error("⚠️ Please fill in all required fields (*).")
                is_valid = False
            
            # Basic phone validation (digits and length check)
            if is_valid and (not phone_number.isdigit() or len(phone_number) < 10):
                error_placeholder.error("⚠️ Please enter a valid phone number (digits only, at least 10).")
                is_valid = False
            
            # Basic email validation
            if is_valid and not re.match(EMAIL_REGEX, email):
                error_placeholder.error("⚠️ Please enter a valid email address.")
                is_valid = False
            
            if is_valid:
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
# 7. STEP 2: Secondary Details Form
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
    default_gender = get_val('gender', 'Male')
    default_gender_index = gender_options.index(default_gender) if default_gender in gender_options else 0
        
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
            message_placeholder.info("Processing registration and saving data...")
            if save_visitor_data_to_db(final_data):
                message_placeholder.success("🎉 Visitor Registration Complete! You are now checked in.")
                st.balloons()
                
                # Clear session state for next registration and trigger redirect
                st.session_state['registration_step'] = 'primary'
                st.session_state['visitor_data'] = {}
                
                # Give user a moment to see the success message before redirecting
                st.snow()
                st.warning("Returning to Main Menu in 3 seconds...")
                import time
                time.sleep(3)
                
            else:
                # Error already displayed in save_visitor_data_to_db
                message_placeholder.error("Registration failed due to a database error. Please try again.")
            
            st.rerun()

# ==============================================================================
# 8. REGISTRATION FLOW ENCAPSULATION
# ==============================================================================

def render_registration_flow():
    """Encapsulates the rendering logic for the multi-step visitor registration form."""
    
    render_step_navigation(st.session_state['registration_step'])

    if st.session_state['registration_step'] == 'primary':
        render_primary_details_form()
    
    elif st.session_state['registration_step'] == 'secondary':
        render_secondary_details_form()


# ==============================================================================
# 9. Main Application Logic
# ==============================================================================

def main_app_flow():
    """Main function to run the application, handling flow between menu and registration."""
    
    # 1. Initialize State
    initialize_session_state()
    
    # 2. ENFORCE LOGIN AND COMPANY ID CHECK
    if not st.session_state.get('admin_logged_in'):
        st.error("Access Denied: Please log in as an Admin to register visitors.")
        st.rerun()
        return
        
    # CRITICAL: Must have a company_id to associate the visitor with.
    company_id = st.session_state.get('company_id')
    if not company_id:
        st.error("Session missing Company ID. Please log in again.")
        st.rerun()
        return
        
    # 3. Connection Test (Stops app if connection fails)
    # This also handles credential retrieval via the caching mechanism
    conn = get_fast_connection()
    if conn is None:
        return # App should already be stopped by get_fast_connection

    # 4. Render Main Header (Always render the main banner)
    render_app_header()
    
    st.info(f"Logged in for Company ID: **{company_id}**")
    
    # 5. Route based on App Flow state
    if st.session_state['app_flow'] == 'menu':
        render_admin_main_screen()
    
    elif st.session_state['app_flow'] == 'registration':
        render_registration_flow()
    

if __name__ == "__main__":
    # --- Mock login state for testing ---
    if 'admin_logged_in' not in st.session_state:
        st.session_state['admin_logged_in'] = True
        # Set the mock company ID explicitly to 1 for testing the constraint
        st.session_state['company_id'] = 1
        
    main_app_flow()
