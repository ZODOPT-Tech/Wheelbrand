import streamlit as st
import os
import mysql.connector
import bcrypt
import boto3
import json
import traceback
from time import sleep
from datetime import datetime, timedelta
import secrets

# ==============================================================================
# 1. CONFIGURATION & CREDENTIALS
# ==============================================================================

# --- AWS & DB Configuration ---
# IMPORTANT: Replace these with your actual AWS region and secret name
AWS_REGION = "ap-south-1" 
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS" 

# --- Configuration (Shared Constants) ---
# The logo path and placeholder text confirmed by the user
LOGO_PATH = "zodopt.png" 
LOGO_PLACEHOLDER_TEXT = "zodopt"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)" # Primary Color for header and main buttons
MIN_PASSWORD_LENGTH = 8
DEFAULT_DB_PORT = 3306 # Standard MySQL port

# --- AWS SECRET MANAGER ----------------
@st.cache_resource
def get_db_credentials():
    """
    Loads DB credentials from AWS Secrets Manager.
    Secret must be a JSON string with keys:
    DB_HOST, DB_NAME, DB_USER, DB_PASSWORD
    
    If credentials cannot be obtained, the app execution is halted.
    """
    if not AWS_SECRET_NAME:
        st.error("FATAL: AWS_SECRET_NAME is not configured. Cannot proceed with database connection.")
        st.stop()
        
    try:
        # Initialize AWS Secrets Manager client
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        
        # Fetch the secret value.
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        
        # SecretsManager stores text in 'SecretString'
        if "SecretString" not in resp:
            raise RuntimeError("SecretString missing in AWS secrets response.")
            
        creds = json.loads(resp["SecretString"])
        required_keys = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        
        for k in required_keys:
            if k not in creds:
                raise RuntimeError(f"Missing required database key in secret: {k}")
                
        return creds
        
    except Exception as e:
        # Display a user-friendly error in Streamlit
        st.error(f"FATAL: Configuration Error: Could not retrieve database credentials from AWS Secrets Manager.")
        st.info("Please verify the AWS_REGION, AWS_SECRET_NAME, and IAM permissions.")
        st.write(f"Details: {e}")
        # Log the full traceback for the developer in the console
        st.write(traceback.format_exc())
        st.stop()


# ---------------- FAST DB CONNECTION ----------------
@st.cache_resource
def get_fast_connection():
    """
    Returns a persistent MySQL connection object (cached by Streamlit).
    This function establishes the connection using credentials from Secrets Manager.
    Stops execution if connection fails.
    """
    credentials = get_db_credentials() # Retrieve creds using the strict AWS function
    
    try:
        conn = mysql.connector.connect(
            host=credentials["DB_HOST"],
            user=credentials["DB_USER"],
            password=credentials["DB_PASSWORD"],
            database=credentials["DB_NAME"],
            port=DEFAULT_DB_PORT,
            autocommit=True, # Ensure changes are saved immediately
            connection_timeout=10,
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"FATAL: Database Connection Error: Cannot connect to MySQL.")
        st.info(f"Please check credentials, database name ('{credentials['DB_NAME']}'), and network access.")
        st.write(f"Error Details: {err.msg}")
        st.stop()
    except Exception as e:
        st.error(f"FATAL: Unexpected Connection Error: {e}")
        st.stop()


# ==============================================================================
# 2. SECURITY AND UTILITY HELPERS
# ==============================================================================

def hash_password(password):
    """Hashes a plaintext password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

def check_password(password, hashed_password):
    """Verifies a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def _get_image_base64(path):
    """Converts a local image file to a base64 string for embedding (Placeholder)."""
    # In this environment, we use a placeholder handler
    return "" 

def set_auth_view(view):
    """Changes the current view and forces a Streamlit re-render."""
    st.session_state['visitor_auth_view'] = view
    # Clear reset state when changing views
    if 'reset_user_id' in st.session_state:
        del st.session_state['reset_user_id']
    sleep(0.1) 
    st.rerun()

# ==============================================================================
# 3. DB INTERACTION FUNCTIONS
# ==============================================================================

# Assumed Schema (Based on current app logic):
# - admin_users: (id, company_id, name, email, password_hash, is_active=1)
# - companies: (id, company_name)

def get_admin_by_email(conn, email):
    """Fetches user ID, hash, name, and company details for login/lookup."""
    cursor = conn.cursor(dictionary=True) 
    query = """
    SELECT au.id, au.password_hash, au.name, c.id AS company_id, c.company_name
    FROM admin_users au
    JOIN companies c ON au.company_id = c.id
    WHERE au.email = %s AND au.is_active = 1;
    """
    try:
        cursor.execute(query, (email.lower(),))
        return cursor.fetchone()
    except Exception as e:
        st.error(f"DB Error fetching admin: {e}")
        return None
    finally:
        cursor.close()

def create_company_and_admin(conn, company_name, admin_name, email, password_hash):
    """Inserts a new company and its first admin user within a single transaction."""
    cursor = conn.cursor()
    try:
        # 1. Insert Company
        company_query = "INSERT INTO companies (company_name) VALUES (%s)"
        cursor.execute(company_query, (company_name,))
        company_id = cursor.lastrowid # Get the ID of the new company

        # 2. Insert Admin User
        admin_query = """
        INSERT INTO admin_users (company_id, name, email, password_hash, is_active)
        VALUES (%s, %s, %s, %s, 1)
        """
        cursor.execute(admin_query, (company_id, admin_name, email.lower(), password_hash))

        conn.commit()
        return True
    except mysql.connector.Error as err:
        conn.rollback()
        # Check for duplicate entry error (1062) for unique fields (email, company_name)
        if err.errno == 1062:
            st.error("Registration failed: An account with this email or company name already exists.")
        else:
            st.error(f"Registration failed (DB error): {err.msg}")
            # Log the full traceback for debugging the transaction failure
            st.error(f"Full Error Trace: {traceback.format_exc()}")
        return False
    except Exception as e:
        conn.rollback()
        st.error(f"Registration failed (General error): {e}")
        return False
    finally:
        cursor.close()

def update_admin_password_directly(conn, user_id, new_password_hash):
    """Updates the admin's password hash directly by user ID (simplified reset)."""
    cursor = conn.cursor()
    update_admin_query = "UPDATE admin_users SET password_hash = %s WHERE id = %s"
    try:
        cursor.execute(update_admin_query, (new_password_hash, user_id))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"DB Error during direct password update: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()


# ==============================================================================
# 4. STREAMLIT VIEW RENDERING FUNCTIONS
# ==============================================================================

def render_admin_register_view():
    """Renders the form for registering a new Company and its initial Admin user."""
    conn = get_fast_connection() 
    
    with st.form("admin_register_form"):
        st.markdown("**Company and Admin Details**")
        
        company_name = st.text_input("Company Name", key="reg_company_name")
        admin_name = st.text_input("Admin Full Name", key="reg_admin_name")
        admin_email = st.text_input("Email ID (Used for Login)", key="reg_admin_email").lower()
        
        st.markdown("---")
        
        password = st.text_input(f"Password (min {MIN_PASSWORD_LENGTH} chars)", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
        
        submitted = st.form_submit_button("Create Company & Admin Account", type="primary")
        
        if submitted:
            if not all([company_name, admin_name, admin_email, password, confirm_password]):
                st.error("Please fill in all required fields.")
                return
            elif password != confirm_password:
                st.error("Passwords do not match.")
                return
            elif len(password) < MIN_PASSWORD_LENGTH:
                st.error(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")
                return

            hashed_pass = hash_password(password)
            
            if create_company_and_admin(conn, company_name, admin_name, admin_email, hashed_pass):
                st.success(f"Company '{company_name}' and Admin '{admin_name}' successfully registered!")
                st.info("You can now sign in using your Email ID.")
                set_auth_view('admin_login') 
            return
    
    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Existing Admin Login", key="existing_admin_login_btn", use_container_width=True):
            set_auth_view('admin_login')
    with col2:
        if st.button("Forgot Password?", key="admin_forgot_pass_btn", use_container_width=True):
            set_auth_view('forgot_password')


def render_existing_admin_login_view():
    """
    Renders the Admin login form for existing users and handles DB authentication.
    """
    conn = get_fast_connection() 

    with st.form("admin_login_form"):
        email = st.text_input("Admin Email ID", key="admin_login_email").lower()
        password = st.text_input("Password", type="password", key="admin_login_password")
        
        submitted = st.form_submit_button("Admin Sign In →", type="primary")
        
        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
                return

            user_data = get_admin_by_email(conn, email)

            if user_data:
                stored_hash = user_data['password_hash']
                is_authenticated = check_password(password, stored_hash)

                if is_authenticated:
                    # Successful Login 
                    st.session_state['admin_logged_in'] = True
                    st.session_state['admin_id'] = user_data['id']
                    st.session_state['admin_email'] = email
                    st.session_state['admin_name'] = user_data['name']
                    st.session_state['company_id'] = user_data['company_id']
                    st.session_state['company_name'] = user_data['company_name']
                    st.success(f"Welcome, {st.session_state['admin_name']}! Redirecting to dashboard...")
                    
                    # Navigate to the dashboard view
                    set_auth_view('visitor_dashboard') 
                    return
                else:
                    st.error("Invalid Admin Email ID or Password.")
            else:
                st.error("Invalid Admin Email ID or Password.")
    
    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← New Registration", key="admin_new_reg_btn", use_container_width=True):
            set_auth_view('admin_register')
    with col2:
        if st.button("Forgot Password?", key="admin_forgot_pass_link", use_container_width=True):
            set_auth_view('forgot_password')

def render_visitor_dashboard_view():
    """
    The main hub for the logged-in administrator.
    (This function simulates the target 'visitor_dashboard' module's 'render_dashboard' function).
    """
    # Enforce login
    if not st.session_state.get('admin_logged_in'):
        st.warning("Please log in to view the dashboard.")
        set_auth_view('admin_login')
        return

    company_name = st.session_state.get('company_name', 'Your Company')
    admin_name = st.session_state.get('admin_name', 'Admin')

    # Placeholder content simulating the 'visitor_dashboard' module's output
    st.markdown(f"## 📊 {company_name} - Visitor Management Dashboard")
    st.markdown(f"Welcome, **{admin_name}**. This is the main dashboard area.")
    st.markdown("---")
    
    st.info("Content from the actual visitor management dashboard module would load here.")

    st.markdown('<div style="margin-top: 50px;"></div>', unsafe_allow_html=True)
    if st.button("← Logout", key="dashboard_logout_btn", use_container_width=True):
        # Clear all admin session state
        for key in ['admin_logged_in', 'admin_id', 'admin_email', 'admin_name', 'company_id', 'company_name']:
            if key in st.session_state:
                del st.session_state[key]
        set_auth_view('admin_login') # Redirect to the login page


def render_forgot_password_view():
    """
    Renders the simplified TWO-STEP password reset flow:
    1. Check email existence.
    2. Allow direct password change if email is found.
    """
    st.warning("⚠️ **ADMIN OVERRIDE:** This simplified two-step flow allows direct password reset by only verifying the email's existence in the database. This is HIGHLY INSECURE for a real application.")
    
    conn = get_fast_connection()

    # --- STAGE 1: EMAIL VERIFICATION ---
    if 'reset_user_id' not in st.session_state:
        st.session_state['reset_user_id'] = None

    if st.session_state['reset_user_id'] is None:
        st.subheader("1. Verify Email ID")
        with st.form("forgot_pass_verify_form"):
            email_to_check = st.text_input("Enter your Admin Email ID", key="forgot_email_input").lower()
            submitted = st.form_submit_button("Check Email Existence", type="primary")

            if submitted:
                if not email_to_check:
                    st.error("Please enter an email address for lookup.")
                    return
                
                user_data = get_admin_by_email(conn, email_to_check)
                
                if user_data:
                    st.session_state['reset_user_id'] = user_data['id']
                    st.success("✅ Email ID verified! You can now set your new password below.")
                    # Force a re-run to display the next step
                    st.rerun() 
                else:
                    st.error("Email ID not found in our records.")
    
    # --- STAGE 2: PASSWORD RESET ---
    if st.session_state['reset_user_id'] is not None:
        st.subheader("2. Set New Password")
        user_id_to_reset = st.session_state['reset_user_id']

        with st.form("forgot_pass_reset_form"):
            # New password fields
            new_password = st.text_input(f"New Password (min {MIN_PASSWORD_LENGTH} chars)", type="password", key="reset_new_password")
            confirm_password = st.text_input("Confirm New Password", type="password", key="reset_confirm_password")
            
            submitted = st.form_submit_button("Finalize Password Reset", type="primary")
            
            if submitted:
                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                    return
                elif len(new_password) < MIN_PASSWORD_LENGTH:
                    st.error(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
                    return

                new_hash = hash_password(new_password)

                # --- ACTUAL DB INTERACTION POINT (Direct Password Update) ---
                if update_admin_password_directly(conn, user_id_to_reset, new_hash):
                    st.success("Password successfully changed! Redirecting to login...")
                    # Clear state and redirect
                    del st.session_state['reset_user_id']
                    set_auth_view('admin_login')
                else:
                    st.error("Password reset failed due to a database error. Please check logs.")
        
    st.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)
    if st.button("← Back to Admin Login", key="forgot_back_login_btn", use_container_width=True):
        set_auth_view('admin_login')

# ==============================================================================
# 5. MAIN APPLICATION ENTRY POINT (CSS/HTML is correctly applied)
# ==============================================================================

def render_visitor_login_page():
    # --- Default view is 'admin_login' ---
    if 'visitor_auth_view' not in st.session_state:
        st.session_state['visitor_auth_view'] = 'admin_login'

    view = st.session_state['visitor_auth_view']
    if view == 'admin_register':
        header_title = "VISITOR MANAGEMENT - ADMIN REGISTRATION"
    elif view == 'admin_login':
        header_title = "VISITOR MANAGEMENT - ADMIN LOGIN"
    elif view == 'visitor_dashboard':
        header_title = "VISITOR MANAGEMENT - DASHBOARD" 
    elif view == 'forgot_password':
        header_title = "VISITOR MANAGEMENT - RESET PASSWORD"
        
    # 1. Inject Custom CSS for styling
    st.markdown(f"""
    <style>
    /* CSS variables for consistency */
    :root {{
        --header-gradient: {HEADER_GRADIENT};
        --primary-color: #50309D;
        --secondary-color: #7A42FF;
        --header-box-shadow: 0 4px 10px rgba(80, 48, 157, 0.4);
    }}

    /* Streamlit layout reset */
    html, body, .stApp .main {{ padding-top: 0px !important; margin-top: 0px !important; }}
    .stApp > header {{ visibility: hidden; }}
    
    /* Header Box - Full Width Design */
    .header-box {{
        background: var(--header-gradient);
        padding: 20px 40px;
        margin-top: 0px; 
        margin-bottom: 40px;
        border-radius: 0 0 15px 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: calc(100% + 4rem); 
        margin-left: -2rem; 
        margin-right: -2rem; 
    }}
    .header-title {{
        font-family: 'Inter', sans-serif; 
        font-size: 30px;
        font-weight: 800;
        color: #FFFFFF; 
        letter-spacing: 1.5px;
        margin: 0;
    }}
    .header-logo-container {{
        font-size: 20px;
        font-weight: bold;
        color: #FFFFFF;
    }}
    
    /* Form and Input Styling */
    .stTextInput input, .stTextArea textarea {{
        font-family: 'Inter', sans-serif;
        background-color: #f0f2f6;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px 15px;
        font-size: 16px;
    }}
    .stTextInput input:focus, .stTextArea textarea:focus {{
        border-color: var(--secondary-color);
        box-shadow: 0 0 0 2px rgba(122, 66, 255, 0.4);
        outline: none;
    }}
    
    /* Primary Button Style (Gradient) */
    .stForm button[kind="primary"],
    .stButton > button:not([key*="back_login_btn"]):not([key*="logout_btn"]):not([key*="existing_admin_login_btn"]):not([key*="checkin_back_dash_btn"]):not([key*="admin_new_reg_btn"]) {{
        background: var(--header-gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 20px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        box-shadow: var(--header-box-shadow) !important;
        margin-top: 20px !important;
        width: 100% !important;
        transition: all 0.2s ease;
    }}
    .stForm button[kind="primary"]:hover,
    .stButton > button:not([key*="back_login_btn"]):not([key*="logout_btn"]):not([key*="existing_admin_login_btn"]):not([key*="checkin_back_dash_btn"]):not([key*="admin_new_reg_btn"]):hover {{
        opacity: 0.9;
        transform: translateY(-2px);
    }}
    
    /* Secondary (Back/Login/Logout) Buttons */
    .stButton > button[key*="back_login_btn"],
    .stButton > button[key*="logout_btn"],
    .stButton > button[key*="existing_admin_login_btn"],
    .stButton > button[key*="admin_new_reg_btn"],
    .stButton > button[key*="checkin_back_dash_btn"] {{
        background: #FFFFFF !important; 
        color: #555555 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        border: 1px solid #E0E0E0 !important;
        font-weight: 500 !important;
        padding: 8px 15px !important;
        margin-top: 10px !important;
        font-size: 14px !important;
        width: 100%;
    }}
    </style>
    """, unsafe_allow_html=True)


    # 2. HEADER 
    logo_base64 = _get_image_base64(LOGO_PATH)
    if logo_base64:
        logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="header-logo-img" style="height: 50px; border-radius: 8px;">'
    else:
        logo_html = f'<div class="header-logo-container">**{LOGO_PLACEHOLDER_TEXT}**</div>'

    st.markdown(
        f"""
        <div class="header-box">
            <div class="header-title">{header_title}</div> 
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3. Dynamic View Rendering
    if view == 'admin_register':
        render_admin_register_view()
    elif view == 'admin_login':
        render_existing_admin_login_view()
    elif view == 'visitor_dashboard':
        render_visitor_dashboard_view()
    elif view == 'forgot_password':
        render_forgot_password_view()
        
if __name__ == '__main__':
    render_visitor_login_page()
