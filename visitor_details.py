import streamlit as st
import base64
from pathlib import Path
import mysql.connector
from datetime import datetime
from mysql.connector import Error
import json
import boto3
from botocore.exceptions import ClientError
import traceback

# Placeholder path
LOGO_PATH = "zodopt.png"  

# ==============================================================================
# 1. CONFIGURATION & CREDENTIALS (AWS Integration)
# ==============================================================================

AWS_REGION = "ap-south-1" 
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS" 
DEFAULT_DB_PORT = 3306

@st.cache_resource(ttl=3600) 
def get_db_credentials():
    """Retrieves database credentials ONLY from AWS Secrets Manager."""
    
    try:
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
    """
    Returns a persistent MySQL connection object by fetching credentials from AWS.
    This function will now halt the app if credential retrieval fails.
    """
    try:
        credentials = get_db_credentials()
        
        conn = mysql.connector.connect(
            host=credentials["DB_HOST"],
            user=credentials["DB_USER"],
            password=credentials["DB_PASSWORD"],
            database=credentials["DB_NAME"],
            port=DEFAULT_DB_PORT,
            autocommit=True,
            connection_timeout=10,
        )
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
    # Note: 'current_page' is initialized in the main application script.
    
    if 'registration_step' not in st.session_state:
        st.session_state['registration_step'] = 'primary'
    if 'visitor_data' not in st.session_state:
        st.session_state['visitor_data'] = {}
    if 'company_id' not in st.session_state:
        st.session_state['company_id'] = None 

# --- NEW HELPER FUNCTION FOR NAVIGATION ---
def navigate_to_main_screen():
    """Clears registration specific state and redirects to the main entry point."""
    
    # 1. Clear ALL session state related to the current registration
    keys_to_clear = [
        'registration_step', 'visitor_data'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # 2. Set the main navigation key
    # IMPORTANT: We must NOT clear global keys like 'admin_logged_in' or 'company_id'
    # if we want the user to remain logged in.
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
    
    cursor = conn.cursor()
    
    fields = (
        "company_id", "registration_timestamp", "full_name", "phone_number", "email", 
        "visit_type", "from_company", "department", "designation", "address_line_1", 
        "city", "state", "postal_code", "country", "gender", "purpose", 
        "person_to_meet", "has_bags", "has_documents", "has_electronic_items", 
        "has_laptop", "has_charger", "has_power_bank"
    )
    
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
        pass 


# ==============================================================================
# 4. HELPER FUNCTIONS (CSS and Header)
# ==============================================================================

def img_to_base64(img_path):
    """Converts a local image file to a base64 string for CSS embedding."""
    return "" 

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

# ==============================================================================
# 5. STEP 1: Primary Details Form
# ==============================================================================

def render_primary_details_form():
    """Renders the Name, Phone, and Email form fields."""
    
    with st.container(border=False):
        
        # --- RESET/NAVIGATION BUTTON LOGIC (Must be outside st.form) ---
        col_reset, col_spacer_check, col_next_placeholder = st.columns([1, 2, 1])
        
        with col_reset:
            # We change this to trigger the hard reset helper function
            reset_clicked = st.button("Reset / Main Menu", use_container_width=True, key="reset_primary")

        if reset_clicked:
            navigate_to_main_screen() # Hard reset and navigate
            # The st.rerun() is inside the helper, so no need for it here.
        # -------------------------------------------------------------
        
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
                st.write("Phone *") 
                st.text_input("Country Code", value="+91", disabled=True, label_visibility="collapsed",
                              help="Country Code (default +91)") 
            with col_number:
                st.write("<br>", unsafe_allow_html=True)
                phone_number = st.text_input("Phone Number", key="phone_input", placeholder="81234 56789", 
                                             value=st.session_state['visitor_data'].get('phone', ''), label_visibility="collapsed")

            # 3. Email
            st.write("Email *")
            email = st.text_input("Email", key="email_input", placeholder="your.email@example.com", 
                                     value=st.session_state['visitor_data'].get('email', ''), label_visibility="collapsed")

            # Submit/Next Button Container (This must be INSIDE the form)
            col_spacer, col_next = st.columns([3, 1])
            
            with col_next:
                submitted = st.form_submit_button("Next →", use_container_width=True)

            # --- Logic check for Submission (Next) ---
            if submitted:
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

# ==============================================================================
# 6. STEP 2: Secondary Details Form
# ==============================================================================

def render_secondary_details_form():
    """Renders the Other Details form fields and handles final submission to DB."""
    
    with st.container(border=False):
        st.markdown("### Other Details")

        # --- THE FORM START (Fields and Submit Button are inside) ---
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
            
            # --- SUBMISSION BUTTON (INSIDE the form) ---
            col_prev_btn, col_spacer_submit, col_submit = st.columns([1, 2, 1])
            
            with col_submit:
                submitted = st.form_submit_button("Complete Registration →", use_container_width=True)

            # --- Submission Logic ---
            if submitted:
                # We update the final_data dictionary using the values captured by the form keys
                final_data = st.session_state['visitor_data']
                final_data.update({
                    'visit_type': st.session_state.get('visit_type'),
                    'from_company': st.session_state.get('from_company'),
                    'department': st.session_state.get('department'),
                    'designation': st.session_state.get('designation'),
                    'address_line_1': st.session_state.get('address_line_1'),
                    'city': st.session_state.get('city'),
                    'state': st.session_state.get('state'),
                    'postal_code': st.session_state.get('postal_code'),
                    'country': st.session_state.get('country'),
                    'gender': st.session_state.get('gender'),
                    'purpose': st.session_state.get('purpose'),
                    'person_to_meet': st.session_state.get('person_to_meet'),
                    'has_bags': st.session_state.get('has_bags', False),
                    'has_documents': st.session_state.get('has_documents', False),
                    'has_electronic_items': st.session_state.get('has_electronic_items', False),
                    'has_laptop': st.session_state.get('has_laptop', False),
                    'has_charger': st.session_state.get('has_charger', False),
                    'has_power_bank': st.session_state.get('has_power_bank', False)
                })
                
                if save_visitor_data_to_db(final_data):
                    st.balloons()
                    st.success("🎉 Visitor Registration Complete! Redirecting to Dashboard...")
                    
                    # Clear session state for next registration
                    st.session_state['registration_step'] = 'primary'
                    st.session_state['visitor_data'] = {} 
                    st.session_state['current_page'] = 'visitor_dashboard' # Redirect to dashboard
                
                st.rerun() 
        
        # --- PREVIOUS / MAIN MENU BUTTONS (OUTSIDE the form) ---
        col_prev, col_main_menu, col_end_spacer = st.columns([1, 1, 2])

        with col_prev:
            if st.button("← Previous Step", key='prev_button_secondary', use_container_width=True):
                st.session_state['registration_step'] = 'primary'
                st.rerun()

        with col_main_menu:
            if st.button("Back to Main Menu", key='main_menu_button_secondary', use_container_width=True):
                navigate_to_main_screen()


# ==============================================================================
# 7. Main Application Logic
# ==============================================================================

def render_details_page():
    """Main function to run the multi-step visitor registration form."""
    
    # 1. ENFORCE LOGIN CHECK
    if not st.session_state.get('admin_logged_in'):
        st.error("Access Denied: Please log in as an Admin to register visitors.")
        st.session_state['current_page'] = 'visitor_login'
        st.rerun()
        return
    
    # Check for Company ID which is set during login
    if not st.session_state.get('company_id'):
        st.error("Session missing Company ID. Please log in again.")
        st.session_state['current_page'] = 'visitor_login'
        st.rerun()
        return
        
    # 2. Initialize session state
    initialize_session_state() 
    
    # Attempt to establish connection early
    get_fast_connection()
    
    # 3. Render content
    render_header(st.session_state['registration_step'])

    if st.session_state['registration_step'] == 'primary':
        render_primary_details_form()
    
    elif st.session_state['registration_step'] == 'secondary':
        render_secondary_details_form()
    

if __name__ == "__main__":
    # --- Mock login state for direct file testing ---
    if 'admin_logged_in' not in st.session_state:
        st.session_state['admin_logged_in'] = True
        st.session_state['company_id'] = 1 
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'visitor_details'
        
    render_details_page()
