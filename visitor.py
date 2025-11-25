import streamlit as st
import pandas as pd
from datetime import datetime
import time
import mysql.connector
from mysql.connector import Error
import json
import boto3 # AWS SDK
import bcrypt # For secure password hashing

# --- HARDCODED CONFIGURATION (Backend) ---
# FIX APPLIED: Using the full Secret ARN Resource Name confirmed by the user image.
HARDCODED_SECRET_NAME = 'Wheelbrand-zM6npS' 
HARDCODED_REGION = 'ap-south-1' # Mumbai region
# ----------------------------------------

# --- CONSTANTS ---
LOGIC_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DISPLAY_TIME_FORMAT = '%I:%M %p'
ADMIN_SALT_ROUNDS = 12 

# Define keys expected in your Secrets Manager JSON entry
SECRET_KEYS = {
    'host_key': 'DB_HOST',
    'database_key': 'DB_NAME',
    'user_key': 'DB_USER',
    'password_key': 'DB_PASSWORD'
}

# --- SESSION STATE INITIALIZATION (Guaranteed to run first) ---

def initialize_session_state():
    """Initializes all necessary session state keys to prevent KeyError."""
    # Set safe default values
    if 'config_verified' not in st.session_state:
        st.session_state['config_verified'] = False # Assume false until check passes
    if 'config_error_message' not in st.session_state:
        st.session_state['config_error_message'] = None
    if 'config_check_performed' not in st.session_state:
        st.session_state['config_check_performed'] = False
    
    # UI Flow States
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
    if 'redirect_name' not in st.session_state:
        st.session_state['redirect_name'] = 'Visitor'

# Call initialization immediately to ensure keys exist
initialize_session_state()

# --- DATABASE CONNECTION & OPERATIONS ---

@st.cache_resource
def fetch_db_credentials_from_secrets_manager():
    """Fetches database credentials from AWS Secrets Manager."""
    secret_name = HARDCODED_SECRET_NAME
    region_name = HARDCODED_REGION

    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        # Use the corrected, full resource name here
        secret_response = client.get_secret_value(SecretId=secret_name)
        
        if 'SecretString' in secret_response:
            secret_data = json.loads(secret_response['SecretString'])
            
            db_config = {
                'host': secret_data[SECRET_KEYS['host_key']],
                'database': secret_data[SECRET_KEYS['database_key']],
                'user': secret_data[SECRET_KEYS['user_key']],
                'password': secret_data[SECRET_KEYS['password_key']]
            }
            return db_config, None
        else:
            raise ValueError("SecretString not found in the secret payload.")

    except client.exceptions.ResourceNotFoundException:
        return None, f"AWS Error: Secret '{secret_name}' not found in region {region_name}. Check the exact secret name (resource name)."
    except KeyError as e:
        return None, f"Configuration Error: Missing required key {e} in the AWS Secret JSON."
    except Exception as e:
        # Catch all other errors, including authentication failures (AccessDenied)
        return None, f"AWS/Boto3 Error: Failed to retrieve credentials. Details: {type(e).__name__}: {e}"

@st.cache_resource(ttl=3600) 
def get_db_connection():
    """Establishes and returns a connection to the MySQL database."""
    db_config, error_msg = fetch_db_credentials_from_secrets_manager()
    
    if db_config is None:
        return None, error_msg 
            
    try:
        conn = mysql.connector.connect(**db_config)
        return conn, None
    except Error as e:
        # This catches connection errors (e.g., host unreachable, wrong DB creds from the Secret)
        return None, f"MySQL Connection Error: Failed to connect to DB. Details: {e}"

def create_initial_tables(conn):
    """Ensures necessary tables exist in the database."""
    if conn is None:
        return False, "Cannot create tables: Database connection failed."

    table_sqls = [
        # 1. Admin Table
        """
        CREATE TABLE IF NOT EXISTS admin (
            admin_id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # 2. Visitors Table
        """
        CREATE TABLE IF NOT EXISTS visitors (
            visitor_id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            phone VARCHAR(50),
            company VARCHAR(255),
            designation VARCHAR(100),
            department VARCHAR(100),
            gender VARCHAR(50) DEFAULT 'Prefer not to say',
            host_to_meet VARCHAR(255) NOT NULL,
            visit_type VARCHAR(50) DEFAULT 'Visitor',
            purpose TEXT,
            address TEXT,
            has_laptop TINYINT(1) DEFAULT 0,
            has_documents TINYINT(1) DEFAULT 0,
            has_powerbank TINYINT(1) DEFAULT 0,
            has_other_bags TINYINT(1) DEFAULT 0,
            digital_signature TEXT NOT NULL,
            registration_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # 3. Visitor Log Table
        """
        CREATE TABLE IF NOT EXISTS visitor_log (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            visitor_id INT NOT NULL,
            visitor_name VARCHAR(255) NOT NULL,
            host VARCHAR(255) NOT NULL,
            company VARCHAR(255),
            time_in_logic DATETIME NOT NULL,
            time_in_display VARCHAR(255) NOT NULL,
            time_out_logic DATETIME,
            time_out_display VARCHAR(255),
            status VARCHAR(50) NOT NULL,
            log_key VARCHAR(255) NOT NULL,
            FOREIGN KEY (visitor_id) REFERENCES visitors(visitor_id)
        )
        """
    ]

    try:
        cursor = conn.cursor()
        for sql in table_sqls:
            cursor.execute(sql)
        conn.commit()
        return True, None
    except Error as e:
        return False, f"Database Initialization Error: Failed to create tables. Details: {e}"
    finally:
        if conn and conn.is_connected():
            cursor.close()


def verify_admin_login(email, password):
    """Checks admin credentials against the 'admin' table using bcrypt."""
    conn, conn_err = get_db_connection()
    if conn is None: 
        return False, conn_err
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT password_hash FROM admin WHERE email = %s" 
        cursor.execute(query, (email,))
        result = cursor.fetchone()

        if result:
            stored_hash = result['password_hash'].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                return True, None
        
        return False, "Invalid email or password."
    except Error as e:
        return False, f"Database error during login: {e}"
    except Exception as e:
        return False, f"An internal error occurred: {e}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def register_admin_user(name, email, password):
    """Registers a new admin user and hashes the password."""
    conn, conn_err = get_db_connection()
    if conn is None: 
        return False, conn_err

    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(ADMIN_SALT_ROUNDS)).decode('utf-8')
        
        cursor = conn.cursor()
        query = "INSERT INTO admin (full_name, email, password_hash) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, email, hashed_password))
        conn.commit()
        return True, "Account created successfully!"
    except Error as e:
        conn.rollback()
        if 'Duplicate entry' in str(e) and 'email' in str(e):
            return False, "This email is already registered."
        return False, f"Database error during registration: {e}"
    except Exception as e:
        return False, f"An internal error occurred: {e}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def save_new_visitor(data):
    """Saves visitor details to 'visitors' and logs the check-in to 'visitor_log'."""
    conn, conn_err = get_db_connection()
    if conn is None: 
        return False, conn_err

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
        return True, data.get('name') 
    except Error as e:
        conn.rollback()
        st.error(f"Database error during visitor registration. Transaction rolled back: {e}")
        return False, None
    except Exception as e:
        return False, f"An internal error occurred: {e}"
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

# --- CSS STYLING & UI COMPONENTS ---

def load_custom_css():
    st.markdown("""
        <style>
        /* Hide Streamlit header/footer and sidebar */
        [data-testid="stSidebar"] { display: none } 
        header, footer { visibility: hidden; }
        
        /* Ensure the main content uses full width */
        .block-container {
            padding-top: 2rem !important; 
            padding-bottom: 2rem !important; 
            max-width: 100% !important; 
        }
        
        /* General styling */
        .stApp { background-color: #F4F7FE; }
        .visitor-header {
            background: linear-gradient(90deg, #4A56E2 0%, #7B4AE2 100%);
            padding: 25px; border-radius: 12px 12px 0 0; color: white;
            margin: -2.5rem -2.5rem 2rem -2.5rem; 
        }
        /* Styling for the unified action container */
        .action-container {
            border-top: 1px solid #eee;
            padding-top: 15px;
            margin-top: 15px;
        }
        
        /* White container for inputs */
        .white-container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }

        /* Button styling - using a consistent purple for all primary actions */
        div.stButton > button[kind="primary"] {
            width: 100%; height: 48px; font-weight: 600;
            background-color: #7C4AE2; /* Solid purple */
            border: none; color: white; border-radius: 8px;
            transition: background-color 0.2s;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #6A3CD4; /* Slightly darker for hover */
        }
        div.stButton > button[kind="secondary"] {
            width: 100%; height: 48px; font-weight: 500;
            background-color: transparent; color: #666; border: 1px solid #ddd;
            border-radius: 8px;
            transition: background-color 0.2s, color 0.2s;
        }
        div.stButton > button[kind="secondary"]:hover {
            background-color: #f0f0f0;
            color: #333;
        }
        </style>
    """, unsafe_allow_html=True)

def render_auth_header(icon, title, subtitle):
    """Renders the authentication screen header."""
    st.markdown(f"""
        <div class="visitor-header">
            <div style="display: flex; align-items: center; justify-content: flex-start;">
                <span style="font-size: 2.5rem; margin-right: 15px;">{icon}</span>
                <div>
                    <h2 style="margin: 0; padding: 0; font-weight: 600;">{title}</h2>
                    <p style="margin: 0; padding: 0; font-size: 0.9em; opacity: 0.9;">{subtitle}</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_custom_header(title, subtitle="Please fill in your details"):
    """Renders the standard registration header."""
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
        active_style = "color: #4A56E2; border-bottom: 3px solid #7B4AE2;" if current_step == step_num else "color: #aaa; border-bottom: none;"
        return f'<div style="font-weight: 600; {active_style} padding-bottom: 12px; text-align: center; font-size: 0.9rem;">{label}</div>'

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
                    st.markdown("<div class='white-container'>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    email = st.text_input("Email Address", placeholder="you@company.com", label_visibility="collapsed")
                    password = st.text_input("Password", type="password", placeholder="Enter your password", label_visibility="collapsed")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    submit = st.form_submit_button("Sign In →", type="primary", use_container_width=True)
                    
                    if submit:
                        is_valid, message = verify_admin_login(email, password)
                        if is_valid:
                            st.session_state['visitor_logged_in'] = True
                            st.rerun()
                        else:
                            st.error(message)
                            
                st.markdown("<div class='action-container' style='border-top: none; padding-top: 0;'>", unsafe_allow_html=True)
                if st.button("Don't have an account? Register", key="login_to_register_btn", type="secondary", use_container_width=True):
                    st.session_state['auth_mode'] = 'register'
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                            
            # --- VIEW: REGISTER ---
            elif st.session_state['auth_mode'] == 'register':
                
                with st.form("register_form"):
                    st.markdown("<div class='white-container'>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    reg_name = st.text_input("Full Name", placeholder="John Doe", label_visibility="collapsed")
                    reg_email = st.text_input("Email Address", placeholder="you@company.com", label_visibility="collapsed")
                    reg_pass = st.text_input("Password", type="password", placeholder="Create a password", label_visibility="collapsed")
                    reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", label_visibility="collapsed")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    submit = st.form_submit_button("Register & Login →", type="primary", use_container_width=True)

                    if submit:
                        if reg_name and reg_email and reg_pass:
                            if reg_pass == reg_confirm:
                                success, message = register_admin_user(reg_name, reg_email, reg_pass)
                                
                                if success:
                                    st.success(message)
                                    time.sleep(1) 
                                    st.session_state['visitor_logged_in'] = True
                                    st.session_state['auth_mode'] = 'login' 
                                    st.rerun()
                                else:
                                    st.error(message)
                            else:
                                st.error("Passwords do not match.")
                        else:
                            st.error("Please fill in all fields.")
                            
                st.markdown("<div class='action-container' style='border-top: none; padding-top: 0;'>", unsafe_allow_html=True)
                if st.button("Already have an account? Sign In", key="register_to_login_btn", type="secondary", use_container_width=True):
                    st.session_state['auth_mode'] = 'login'
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

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
                    st.markdown("<div class='white-container'>", unsafe_allow_html=True)
                    st.markdown("##### Contact Information")
                    name = st.text_input("Full Name", value=temp.get('name', ''), placeholder="John Doe")
                    email = st.text_input("Email Address", value=temp.get('email', ''), placeholder="your.email@example.com")
                    phone = st.text_input("Phone Number", value=temp.get('phone', ''), placeholder="81234 56789")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("<div class='action-container'>", unsafe_allow_html=True)
                    b1, b2 = st.columns(2)
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
                    st.markdown("</div>", unsafe_allow_html=True)

            # --- STEP 2: SECONDARY DETAILS ---
            elif step == 2:
                with st.form("step2_form"):
                    st.markdown("<div class='white-container'>", unsafe_allow_html=True)
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
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("<div class='action-container'>", unsafe_allow_html=True)
                    b1, b2 = st.columns(2)
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
                    st.markdown("</div>", unsafe_allow_html=True)

            # --- STEP 3: IDENTITY ---
            elif step == 3:
                with st.form("step3_form"):
                    st.markdown("<div class='white-container'>", unsafe_allow_html=True)
                    st.markdown("##### Identity Verification")
                    
                    st.file_uploader("Upload ID Proof (Optional)", type=['jpg', 'png', 'pdf']) 
                        
                    st.info(f"Confirming check-in for: **{temp.get('name', 'Guest')}**")
                    signature = st.text_area("**Digital Signature (Type Full Name)**", value=temp.get('signature', ''), placeholder="Type your full name as signature")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("<div class='action-container'>", unsafe_allow_html=True)
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.form_submit_button("← Back", type="secondary", use_container_width=True):
                            st.session_state['visitor_form_step'] = 2
                            st.rerun()
                    with b2:
                        if st.form_submit_button("Confirm & Sign In", type="primary", use_container_width=True):
                            if signature.strip() != "":
                                st.session_state['temp_visitor_data']['signature'] = signature
                                
                                success, result = save_new_visitor(st.session_state['temp_visitor_data'])
                                
                                if success:
                                    st.session_state['redirect_name'] = result
                                    st.session_state['registration_complete'] = True
                                    st.rerun()
                                else:
                                    st.error(f"Check-in failed due to a database error: {result}")

                            else:
                                st.error("Digital Signature required to complete check-in.")
                    st.markdown("</div>", unsafe_allow_html=True)

def success_screen():
    load_custom_css()
    col1, col2, col3 = st.columns([1, 1, 1])
    welcome_name = st.session_state.pop('redirect_name', 'Visitor')

    with col2:
        with st.container():
            render_custom_header("Check-in Complete! 🎉", "You may now enter the premises.")
            st.markdown(f"<h2 style='text-align: center;'>Welcome, {welcome_name}!</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #666;'>Your details have been successfully logged.</p>", unsafe_allow_html=True)
            
            st.markdown("<div class='action-container'>", unsafe_allow_html=True)
            
            b1, b2 = st.columns(2)
            
            with b1:
                if st.button("New Visitor Check-in", type="primary", use_container_width=True):
                    st.session_state['registration_complete'] = False
                    st.session_state['visitor_form_step'] = 1
                    st.session_state['temp_visitor_data'] = {}
                    st.rerun()
            with b2:
                if st.button("Log Out (Admin)", type="secondary", use_container_width=True):
                    go_back_to_login()
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

# --- Main App Execution Flow ---

def visitor_page():
    
    # Safely checks the config status
    if not st.session_state['config_verified']:
        st.set_page_config(layout="centered", page_title="Configuration Error")
        st.title("🛑 Fatal Error: Application Not Configured")
        st.error(st.session_state.get('config_error_message', "The application could not retrieve database credentials."))
        st.info(f"Attempted Secret: **{HARDCODED_SECRET_NAME}** in Region: **{HARDCODED_REGION}**")
        st.warning("Please verify your AWS Secrets Manager configuration and IAM permissions/network access.")
        return

    # Main application routing
    if st.session_state['registration_complete']:
        success_screen() 
    elif st.session_state['visitor_logged_in']:
        registration_form_screen() 
    else:
        auth_screen() 

if __name__ == "__main__":
    
    st.set_page_config(layout="wide", page_title="Visitor Management")
    
    # Run the critical config and table check only ONCE on the first run.
    if not st.session_state['config_check_performed']:
        
        # 1. Check AWS Secret access
        db_config, aws_error_msg = fetch_db_credentials_from_secrets_manager()
        
        if db_config is None:
            # AWS Secret retrieval failed
            st.session_state['config_verified'] = False
            st.session_state['config_error_message'] = aws_error_msg
        else:
            # 2. AWS Secret OK, now check DB connection
            conn, conn_error_msg = get_db_connection()
            if conn is None:
                # DB connection failed (Check HOST, USER, PASS from secret)
                st.session_state['config_verified'] = False
                st.session_state['config_error_message'] = conn_error_msg
            else:
                # 3. DB Connection OK, ensure tables exist
                table_success, table_msg = create_initial_tables(conn)
                conn.close() 
                if not table_success:
                    st.session_state['config_verified'] = False
                    st.session_state['config_error_message'] = table_msg
                else:
                    st.session_state['config_verified'] = True
        
        st.session_state['config_check_performed'] = True
        # Rerun to ensure the correct screen (error or main app) loads immediately
        st.rerun() 
    
    # Execute the main app logic
    visitor_page()
