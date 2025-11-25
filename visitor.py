import streamlit as st
import pandas as pd
from datetime import datetime
import time
import mysql.connector
from mysql.connector import Error
import json 
import boto3 # AWS SDK

# --- CONSTANTS ---
LOGIC_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DISPLAY_TIME_FORMAT = '%I:%M %p'

# --- DEFAULT CONFIGURATION ---
# These are the values requested by the user, used as defaults in the sidebar.
DEFAULT_SECRET_NAME = 'Wheelbrand'
DEFAULT_REGION = 'ap-south-1' # Mumbai region

# Define keys expected in your Secrets Manager entry
SECRET_KEYS = {
    'host_key': 'DB_HOST',
    'database_key': 'DB_NAME',
    'user_key': 'DB_USER',
    'password_key': 'DB_PASSWORD'
}

# --- SESSION STATE INITIALIZATION (FOR UI FLOW AND CONFIGURATION ONLY) ---

# Database Configuration State
if 'secret_name' not in st.session_state:
    st.session_state['secret_name'] = DEFAULT_SECRET_NAME
if 'region_name' not in st.session_state:
    st.session_state['region_name'] = DEFAULT_REGION
if 'config_verified' not in st.session_state:
    st.session_state['config_verified'] = False

# Authentication and Form Flow States
if 'visitor_form_step' not in st.session_state:
    st.session_state['visitor_form_step'] = 1
if 'temp_visitor_data' not in st.session_state:
    st.session_state['temp_visitor_data'] = {}
if 'registration_complete' not in st.session_state:
    st.session_state['registration_complete'] = False
if 'visitor_logged_in' not in st.session_state:
    st.session_state['visitor_logged_in'] = False
if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'login' 

# --- DATABASE CONNECTION & OPERATIONS ---

def fetch_db_credentials_from_secrets_manager():
    """
    Fetches database credentials from AWS Secrets Manager using boto3 
    based on user input stored in session state.
    """
    secret_name = st.session_state['secret_name']
    region_name = st.session_state['region_name']

    if not secret_name or not region_name:
        return None, "Secret name and region must be configured."

    try:
        # 1. Initialize AWS Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        
        # 2. Retrieve the secret value
        secret_response = client.get_secret_value(SecretId=secret_name)
        
        if 'SecretString' in secret_response:
            secret_string = secret_response['SecretString']
        else:
            raise ValueError("SecretString not found in the secret payload. Check your secret type.")

        # 3. Parse the JSON string
        secret_data = json.loads(secret_string)
        
        # 4. Map the keys to the format needed for mysql.connector
        db_config = {
            'host': secret_data[SECRET_KEYS['host_key']],
            'database': secret_data[SECRET_KEYS['database_key']],
            'user': secret_data[SECRET_KEYS['user_key']],
            'password': secret_data[SECRET_KEYS['password_key']]
        }
        return db_config, None

    except client.exceptions.ResourceNotFoundException:
        return None, f"AWS Error: The secret '{secret_name}' was not found in region {region_name}."
    except Exception as e:
        return None, f"AWS/Boto3 Error: Failed to retrieve credentials. Check IAM permissions and secret format. Details: {e}"

def get_db_connection():
    """Establishes and returns a connection to the MySQL database."""
    db_config, error_msg = fetch_db_credentials_from_secrets_manager()
    
    if db_config is None:
        if not st.session_state['config_verified']:
            return None
        st.error(f"Database configuration failed: {error_msg}")
        return None
        
    try:
        # Connect using the fetched credentials
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        st.error(f"Error connecting to MySQL with secret credentials. Check host/port/network: {e}")
        return None

def verify_admin_login(email, password):
    """Checks admin credentials against the 'admin' table."""
    conn = get_db_connection()
    if conn is None:
        return False, None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT 1 FROM admin WHERE email = %s AND password_hash = %s" 
        cursor.execute(query, (email, password))
        
        if cursor.fetchone():
            return True, None
        return False, None
    except Error as e:
        st.error(f"Database error during login: {e}")
        return False, None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def register_admin_user(name, email, password):
    """Registers a new admin user into the 'admin' table."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        cursor = conn.cursor()
        query = "INSERT INTO admin (full_name, email, password_hash) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, email, password))
        conn.commit()
        return True, "Account created successfully!"
    except Error as e:
        if 'Duplicate entry' in str(e) and 'email' in str(e):
            return False, "This email is already registered."
        return False, f"Database error during registration: {e}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def save_new_visitor(data):
    """Saves visitor details to 'visitors' and logs the check-in to 'visitor_log'."""
    conn = get_db_connection()
    if conn is None:
        return False, None

    try:
        cursor = conn.cursor()
        
        # 1. Insert into 'visitors' table
        visitor_insert_query = """
        INSERT INTO visitors (
            full_name, email, phone, company, designation, department, gender, 
            host_to_meet, visit_type, purpose, address, has_laptop, 
            has_documents, has_powerbank, has_other_bags, digital_signature
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        # Prepare visitor data (mapping booleans to 1/0 for tinyint(1) columns)
        visitor_data = (
            data.get('name'), data.get('email'), data.get('phone'), data.get('company'), 
            data.get('designation'), data.get('department'), data.get('gender', 'Prefer not to say'), 
            data.get('host'), data.get('visit_type', 'Visitor'), data.get('purpose'), data.get('address'),
            1 if data.get('laptop') else 0, 1 if data.get('documents') else 0, 
            1 if data.get('power') else 0, 1 if data.get('other') else 0, 
            data.get('signature')
        )
        cursor.execute(visitor_insert_query, visitor_data)
        
        new_visitor_id = cursor.lastrowid
        
        # 2. Insert into 'visitor_log' table
        current_time = datetime.now()
        log_key = str(current_time.timestamp()) 

        log_insert_query = """
        INSERT INTO visitor_log (
            visitor_id, visitor_name, host, company, 
            time_in_logic, time_in_display, status, log_key
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        log_data = (
            new_visitor_id, data.get('name'), data.get('host'), data.get('company'),
            current_time.strftime(LOGIC_TIME_FORMAT), current_time.strftime(DISPLAY_TIME_FORMAT),
            'In Office', log_key
        )
        cursor.execute(log_insert_query, log_data)

        conn.commit()
        # Return success flag and the visitor's name (local variable)
        return True, data.get('name') 
    except Error as e:
        conn.rollback()
        st.error(f"Database error during visitor registration: {e}")
        return False, None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- HELPER FUNCTIONS ---

def go_back_to_login():
    """Resets UI state and redirects to login."""
    st.session_state['visitor_logged_in'] = False
    st.session_state['visitor_form_step'] = 1
    st.session_state['temp_visitor_data'] = {}
    st.session_state['registration_complete'] = False
    st.session_state['auth_mode'] = 'login'

def check_db_config():
    """Attempts to fetch credentials to verify configuration."""
    if not st.session_state['secret_name'] or not st.session_state['region_name']:
        st.error("Please enter both the Secret Name and AWS Region.")
        st.session_state['config_verified'] = False
        return

    st.session_state['config_verified'] = True 
    db_config, error_msg = fetch_db_credentials_from_secrets_manager()

    if db_config:
        st.success("Configuration verified! Credentials successfully retrieved from AWS Secrets Manager.")
        st.session_state['config_verified'] = True
    else:
        st.error(f"Configuration Failed. Details: {error_msg}")
        st.session_state['config_verified'] = False

# --- CSS STYLING & UI COMPONENTS ---

def load_custom_css():
    st.markdown("""
        <style>
        /* MAIN CONTAINER SETUP */
        .stApp { background-color: #F4F7FE; }
        .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; max-width: 100% !important; }
        header, footer { visibility: hidden; }
        
        /* CARD STYLING */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
            background-color: white; padding: 2.5rem; border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05); margin-bottom: 2rem;
        }

        /* CUSTOM HEADER GRADIENT */
        .visitor-header {
            background: linear-gradient(90deg, #4A56E2 0%, #7B4AE2 100%);
            padding: 25px; border-radius: 12px 12px 0 0; color: white;
            margin: -2.5rem -2.5rem 2rem -2.5rem; 
        }

        /* FLEX CONTAINER FOR LOGO/TITLE ALIGNMENT */
        .auth-header-content { display: flex; align-items: center; justify-content: flex-start; padding: 0 10px; }
        .auth-icon { font-size: 2.5rem; margin-right: 15px; line-height: 1; }
        .auth-title-box { display: flex; flex-direction: column; }
        .auth-main-title { margin: 0; padding: 0; font-weight: 600; line-height: 1.2; font-size: 1.8rem; }
        .auth-subtitle { margin: 0; padding: 0; font-size: 0.9em; opacity: 0.9; }
        
        /* INPUT FIELDS */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {
            border-radius: 8px; border: 1px solid #E0E0E0; padding: 10px; color: #444;
        }
        
        /* PRIMARY BUTTONS */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #4A56E2 0%, #7B4AE2 100%);
            border: none; color: white; border-radius: 8px; height: 48px;
            font-size: 1rem; font-weight: 600; width: 100%; transition: all 0.3s ease;
        }
        /* SECONDARY BUTTONS */
        div.stButton > button[kind="secondary"] {
            background-color: transparent; color: #666; border: 1px solid #ddd;
            border-radius: 8px; height: 48px; width: 100%;
        }

        /* TABS */
        .nav-tab {
            font-weight: 600; color: #aaa; text-align: center; padding-bottom: 12px;
            cursor: default; font-size: 0.9rem;
        }
        .nav-tab.active {
            color: #4A56E2; border-bottom: 3px solid #7B4AE2;
        }
        </style>
    """, unsafe_allow_html=True)

def render_auth_header(icon, title, subtitle):
    """Renders the header with the icon next to the heading."""
    st.markdown(f"""
        <div class="visitor-header">
            <div class="auth-header-content">
                <span class="auth-icon">{icon}</span>
                <div class="auth-title-box">
                    <h2 class="auth-main-title">{title}</h2>
                    <p class="auth-subtitle">{subtitle}</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_custom_header(title, subtitle="Please fill in your details"):
    """Renders the standard registration header (without icon)."""
    st.markdown(f"""
        <div class="visitor-header">
            <h2 style="margin:0; padding:0; font-weight:600;">{title}</h2>
            <p style="margin:5px 0 0 0; padding:0; font-size: 1em; opacity: 0.9;">{subtitle}</p>
        </div>
    """, unsafe_allow_html=True)

def render_tabs(current_step):
    """Renders the navigation tabs for the multi-step form."""
    c1, c2, c3 = st.columns(3)
    def get_tab_html(label, step_num):
        active_class = "active" if current_step == step_num else ""
        return f'<div class="nav-tab {active_class}">{label}</div>'

    with c1: st.markdown(get_tab_html("PRIMARY DETAILS", 1), unsafe_allow_html=True)
    with c2: st.markdown(get_tab_html("SECONDARY DETAILS", 2), unsafe_allow_html=True)
    with c3: st.markdown(get_tab_html("IDENTITY", 3), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# --- SCREENS ---

def auth_screen():
    load_custom_css()
    
    col1, col2, col3 = st.columns([0.2, 5, 0.2])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        with st.container():
            
            if st.session_state['auth_mode'] == 'login':
                render_auth_header("📅", "**Visitplan** Login", "Sign in to manage your visits")
            else:
                render_auth_header("✍️", "New User Registration", "Create a new admin account")

            # --- VIEW: LOGIN ---
            if st.session_state['auth_mode'] == 'login':
                
                with st.form("login_form"):
                    st.markdown("<br>", unsafe_allow_html=True)
                    email = st.text_input("Email Address", placeholder="you@company.com")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if st.form_submit_button("Sign In →", type="primary", use_container_width=True):
                        # Note: We don't fetch the name, only verification is needed
                        is_valid, _ = verify_admin_login(email, password)
                        
                        if is_valid:
                            st.session_state['visitor_logged_in'] = True
                            st.rerun()
                        else:
                            st.error("Invalid email or password")
                
                st.markdown("---")
                if st.button("Don't have an account? Register", type="secondary", use_container_width=True):
                    st.session_state['auth_mode'] = 'register'
                    st.rerun()

            # --- VIEW: REGISTER ---
            elif st.session_state['auth_mode'] == 'register':
                
                with st.form("register_form"):
                    st.markdown("<br>", unsafe_allow_html=True)
                    reg_name = st.text_input("Full Name", placeholder="John Doe")
                    reg_email = st.text_input("Email Address", placeholder="you@company.com")
                    reg_pass = st.text_input("Password", type="password", placeholder="Create a password")
                    reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if st.form_submit_button("Register & Login →", type="primary", use_container_width=True):
                        if reg_name and reg_email and reg_pass:
                            if reg_pass == reg_confirm:
                                success, message = register_admin_user(reg_name, reg_email, reg_pass)
                                
                                if success:
                                    st.success(message)
                                    time.sleep(1)
                                    st.session_state['visitor_logged_in'] = True
                                    st.rerun()
                                else:
                                    st.error(message)
                            else:
                                st.error("Passwords do not match.")
                        else:
                            st.error("Please fill in all fields.")

                st.markdown("---")
                if st.button("Already have an account? Sign In", type="secondary", use_container_width=True):
                    st.session_state['auth_mode'] = 'login'
                    st.rerun()

def registration_form_screen():
    load_custom_css()
    
    c_left, c_main, c_right = st.columns([0.1, 5, 0.1])
    
    with c_main:
        with st.container():
            render_custom_header("Visitor Check-in", "Please complete the 3-step registration form.")
            render_tabs(st.session_state['visitor_form_step'])
            
            temp = st.session_state['temp_visitor_data']
            step = st.session_state['visitor_form_step']

            # --- STEP 1: PRIMARY DETAILS ---
            if step == 1:
                with st.form("step1_form", clear_on_submit=False):
                    
                    st.markdown("##### Contact Information")
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    name = st.text_input("Full Name", value=temp.get('name', ''), placeholder="John Doe")
                    email = st.text_input("Email Address", value=temp.get('email', ''), placeholder="your.email@example.com")
                    phone = st.text_input("Phone Number", value=temp.get('phone', ''), placeholder="81234 56789")

                    st.markdown("<br><br>", unsafe_allow_html=True)
                    
                    b1, b2 = st.columns([1, 1])
                    with b1:
                        if st.form_submit_button("Reset Form", type="secondary", use_container_width=True):
                            st.session_state['temp_visitor_data'] = {}
                            st.rerun()
                    with b2:
                        if st.form_submit_button("Next Step →", type="primary", use_container_width=True):
                            if phone and email and name:
                                st.session_state['temp_visitor_data'].update({'name': name, 'phone': phone, 'email': email})
                                st.session_state['visitor_form_step'] = 2
                                st.rerun()
                            else:
                                st.warning("Please fill in all required fields.")

            # --- STEP 2: SECONDARY DETAILS ---
            elif step == 2:
                with st.form("step2_form"):
                    st.markdown("##### Organisation Details & Host")
                    
                    c1, c2, c3 = st.columns(3)
                    with c1: company = st.text_input("From Company", value=temp.get('company', ''))
                    with c2: designation = st.text_input("Designation", value=temp.get('designation', '')) 
                    with c3: department = st.text_input("Department", value=temp.get('department', '')) 

                    c4, c5, c6 = st.columns(3)
                    with c4:
                        gender_options = ["Prefer not to say", "Male", "Female", "Other"]
                        default_index = gender_options.index(temp.get('gender', 'Prefer not to say'))
                        gender = st.radio("Gender", gender_options, index=default_index, horizontal=True)

                    with c5: host = st.text_input("**Person to Visit**", value=temp.get('host', ''), placeholder="Enter host name")
                    with c6: visit_type = st.selectbox("Visit Type", ["Vendor", "Customer", "Visitor"], index=["Vendor", "Customer", "Visitor"].index(temp.get('visit_type', 'Visitor')))
                        
                    c7, c8 = st.columns([1, 1])
                    with c7: purpose = st.text_input("Purpose of Visit", value=temp.get('purpose', ''))
                    with c8: address = st.text_area("Organisation Address", value=temp.get('address', ''), placeholder="Full address of your organisation", height=50)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("##### Belongings Declaration")
                    
                    cb1, cb2, cb3, cb4 = st.columns(4)
                    with cb1: bags = st.checkbox("Laptop", value=temp.get('laptop', False))
                    with cb2: docs = st.checkbox("Documents", value=temp.get('documents', False))
                    with cb3: power = st.checkbox("Power Bank", value=temp.get('power', False))
                    with cb4: other = st.checkbox("Other Bags", value=temp.get('other', False))
                    
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    
                    b1, b2 = st.columns([1, 1])
                    with b1:
                        if st.form_submit_button("← Back", type="secondary", use_container_width=True):
                            st.session_state['visitor_form_step'] = 1
                            st.rerun()
                    with b2:
                        if st.form_submit_button("Next Step →", type="primary", use_container_width=True):
                            if host.strip() != "":
                                st.session_state['temp_visitor_data'].update({
                                    'company': company, 'designation': designation,
                                    'department': department, 'visit_type': visit_type, 
                                    'host': host, 'purpose': purpose, 'gender': gender,     
                                    'address': address, 'laptop': bags, 'documents': docs,
                                    'power': power, 'other': other
                                })
                                st.session_state['visitor_form_step'] = 3
                                st.rerun()
                            else:
                                st.error("Please enter the **Person to Visit** (Host).")

            # --- STEP 3: IDENTITY ---
            elif step == 3:
                with st.form("step3_form"):
                    st.markdown("##### Identity Verification")
                    
                    st.file_uploader("Upload ID Proof (Optional)", type=['jpg', 'png', 'pdf']) 
                        
                    st.info(f"Confirming check-in as: **{temp.get('name')}**")
                    signature = st.text_area("**Digital Signature (Type Full Name)**", value=temp.get('signature', ''), placeholder="Type your full name as signature")
                    
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    
                    b1, b2 = st.columns([1, 1])
                    with b1:
                        if st.form_submit_button("← Back", type="secondary", use_container_width=True):
                            st.session_state['visitor_form_step'] = 2
                            st.rerun()
                    with b2:
                        if st.form_submit_button("Confirm & Sign In", type="primary", use_container_width=True):
                            if signature.strip() != "":
                                st.session_state['temp_visitor_data']['signature'] = signature
                                
                                # --- DB SAVE ACTION ---
                                success, last_registered_name = save_new_visitor(st.session_state['temp_visitor_data'])
                                
                                if success:
                                    # Use a temporary key to hold the name for the redirect
                                    st.session_state['redirect_name'] = last_registered_name 
                                    st.session_state['registration_complete'] = True
                                    st.rerun()
                                else:
                                    st.error("Check-in failed due to a database error. Please contact admin.")

                            else:
                                st.error("Digital Signature required to complete check-in.")

def success_screen():
    load_custom_css()
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # Safely retrieve the name, defaulting if not found
    welcome_name = st.session_state.pop('redirect_name', 'Visitor')

    with col2:
        with st.container():
            render_custom_header("Check-in Complete! 🎉", "You may now enter the premises.")
            st.markdown(f"<h2 style='text-align: center;'>Welcome, {welcome_name}!</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #666;'>Your details have been successfully logged.</p>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("New Visitor Check-in", type="primary", use_container_width=True):
                st.session_state['registration_complete'] = False
                st.session_state['visitor_form_step'] = 1
                st.session_state['temp_visitor_data'] = {}
                st.rerun()
            if st.button("Log Out (Admin)", type="secondary", use_container_width=True):
                go_back_to_login()
                st.rerun()


# --- Main App Execution Flow ---

def visitor_page():
    # --- TOP LEVEL CONFIGURATION WIDGET (Sidebar) ---
    
    config_state = "✅ Config Verified" if st.session_state['config_verified'] else "⚠️ Configure Database Connection"
    
    with st.sidebar:
        st.header("⚙️ AWS Secrets Configuration")
        st.caption("Enter the details for your AWS Secrets Manager.")
        with st.form("aws_config_form"):
            st.text_input(
                "AWS Secret Name (or ARN)", 
                key='secret_name', 
                value=st.session_state['secret_name'], 
                placeholder="e.g., my-prod-db-secret"
            )
            st.text_input(
                "AWS Region Name", 
                key='region_name', 
                value=st.session_state['region_name'], 
                placeholder="e.g., ap-south-1 (Mumbai)"
            )
            
            if st.form_submit_button(config_state, type='primary', use_container_width=True):
                check_db_config()
                st.rerun()
        
        if st.session_state['config_verified']:
            st.success("Ready to connect to the database.")
            st.markdown("---")
            if st.session_state['visitor_logged_in']:
                if st.button("Log Out Admin", type='secondary', use_container_width=True):
                    go_back_to_login()
                    st.rerun()
        else:
            st.warning("Please configure and verify the connection settings to proceed.")
            
    # --- MAIN APPLICATION RENDERING ---
    if not st.session_state['config_verified']:
        st.title("Database Configuration Required")
        st.info("Please confirm the AWS Secret Name (`Wheelbrand`) and Region (`ap-south-1`) in the sidebar, then click the button to verify the connection before proceeding to login.")
    elif st.session_state['registration_complete']:
        success_screen() 
    elif st.session_state['visitor_logged_in']:
        registration_form_screen() 
    else:
        auth_screen() 

if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Visitor Management")
    visitor_page()
