import streamlit as st
import os
import mysql.connector
import bcrypt
import boto3
import json
import traceback
from time import sleep
from typing import Dict, Any, Optional, Callable

# ==============================================================================
# 1. CONFIGURATION & CREDENTIALS
# ==============================================================================

# --- AWS & DB Configuration ---
# IMPORTANT: Replace these with your actual AWS region and secret name
AWS_REGION = "ap-south-1" 
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS" 

# --- Configuration (Shared Constants) ---
LOGO_PATH = "zodopt.png" 
LOGO_PLACEHOLDER_TEXT = "zodopt"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)" # Primary Color for header and main buttons
MIN_PASSWORD_LENGTH = 8
DEFAULT_DB_PORT = 3306 # Standard MySQL port

# --- AWS SECRET MANAGER ----------------
@st.cache_resource
def get_db_credentials() -> Dict[str, str]:
    """
    Loads DB credentials from AWS Secrets Manager.
    Secret must be a JSON string with keys: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD.
    
    Stops the app execution if credentials cannot be obtained.
    """
    if not AWS_SECRET_NAME:
        st.error("FATAL: AWS_SECRET_NAME is not configured. Cannot proceed with database connection.")
        st.stop()
        
    try:
        # Initialize AWS Secrets Manager client
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        
        # Fetch the secret value.
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        
        if "SecretString" not in resp:
            raise RuntimeError("SecretString missing in AWS secrets response.")
            
        creds = json.loads(resp["SecretString"])
        required_keys = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        
        for k in required_keys:
            if k not in creds:
                raise RuntimeError(f"Missing required database key in secret: {k}")
                
        return creds
        
    except Exception as e:
        st.error(f"FATAL: Configuration Error: Could not retrieve database credentials from AWS Secrets Manager.")
        st.info("Please verify the AWS_REGION, AWS_SECRET_NAME, and IAM permissions.")
        st.write(f"Details: {e}")
        st.write(traceback.format_exc())
        st.stop()


# ---------------- FAST DB CONNECTION ----------------
@st.cache_resource
def get_fast_connection() -> mysql.connector.connection.MySQLConnection:
    """
    Returns a persistent MySQL connection object (cached by Streamlit).
    Stops execution if connection fails.
    """
    credentials = get_db_credentials()
    
    try:
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

def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    # Use a fixed salt round (12 is secure and common)
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

def check_password(password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        # Catch value errors if hash format is wrong
        return False

def _get_image_base64(path: str) -> str:
    """Converts a local image file to a base64 string for embedding (Placeholder)."""
    # Placeholder implementation returns a small purple square image data URI
    try:
        if os.path.exists(path):
            with open(path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
    except Exception:
        pass
    # Fallback placeholder data
    return "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDTAgAQJUYAKYfBpZZXFw5AAAAAElFTSuQmCC"

def set_auth_view(view: str):
    """Changes the current view and forces a Streamlit re-render."""
    st.session_state['visitor_auth_view'] = view
    # Clear reset state when changing views
    if 'reset_user_id' in st.session_state:
        del st.session_state['reset_user_id']
    sleep(0.01) # Small delay to ensure state update before rerun
    st.rerun()

# ==============================================================================
# 3. DB INTERACTION FUNCTIONS
# ==============================================================================

def get_admin_by_email(conn, email: str) -> Optional[Dict[str, Any]]:
    """Fetches user ID, hash, name, and company details for login/lookup."""
    # Ensure email is lowercased for case-insensitive lookup if DB collation is case-sensitive
    email = email.lower()
    query = """
    SELECT au.id, au.password_hash, au.name, c.id AS company_id, c.company_name
    FROM admin_users au
    JOIN companies c ON au.company_id = c.id
    WHERE au.email = %s AND au.is_active = 1;
    """
    try:
        # Using context manager for cursor ensures it's closed
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, (email,))
            return cursor.fetchone()
    except Exception as e:
        # Log the error, but do not display full trace to end-user unless debugging
        print(f"DB Error fetching admin: {e}")
        return None

def create_company_and_admin(conn, company_name: str, admin_name: str, email: str, password_hash: str) -> bool:
    """Inserts a new company and its first admin user within a single transaction."""
    try:
        with conn.cursor() as cursor:
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
        # Check for duplicate entry error (1062)
        if err.errno == 1062:
            st.error("Registration failed: An account with this email or company name already exists.")
        else:
            st.error(f"Registration failed (DB error): {err.msg}")
            # print(f"Full Error Trace: {traceback.format_exc()}") # Optional: For deeper debugging
        return False
    except Exception as e:
        conn.rollback()
        st.error(f"Registration failed (General error): {e}")
        return False


def update_admin_password_directly(conn, user_id: int, new_password_hash: str) -> bool:
    """Updates the admin's password hash directly by user ID (simplified reset)."""
    update_admin_query = "UPDATE admin_users SET password_hash = %s WHERE id = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(update_admin_query, (new_password_hash, user_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        st.error(f"DB Error during direct password update: {e}")
        conn.rollback()
        return False


# ==============================================================================
# 4. STREAMLIT VIEW RENDERING FUNCTIONS
# ==============================================================================

def render_admin_register_view():
    """Renders the form for registering a new Company and its initial Admin user."""
    conn = get_fast_connection() 
    
    st.subheader("New Admin Registration")
    with st.form("admin_register_form", clear_on_submit=False):
        
        company_name = st.text_input("Company Name", key="reg_company_name_input")
        admin_name = st.text_input("Admin Full Name", key="reg_admin_name_input")
        admin_email = st.text_input("Email ID (Used for Login)", key="reg_admin_email_input").lower()
        
        st.markdown("---")
        
        password = st.text_input(f"Password (min {MIN_PASSWORD_LENGTH} chars)", type="password", key="reg_password_input")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password_input")
        
        submitted = st.form_submit_button("Create Company & Admin Account", type="primary")
        
        if submitted:
            # Basic validation
            if not all([company_name, admin_name, admin_email, password, confirm_password]):
                st.error("Please fill in all required fields.")
                return
            if password != confirm_password:
                st.error("Passwords do not match.")
                return
            if len(password) < MIN_PASSWORD_LENGTH:
                st.error(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")
                return
            
            # Database action
            hashed_pass = hash_password(password)
            
            if create_company_and_admin(conn, company_name, admin_name, admin_email, hashed_pass):
                st.success(f"Company '{company_name}' and Admin '{admin_name}' successfully registered!")
                # Reset form state manually if needed, or rely on clear_on_submit=True/False
                # For this flow, we want to clear fields if successful
                st.session_state["reg_company_name_input"] = ""
                st.session_state["reg_admin_name_input"] = ""
                st.session_state["reg_admin_email_input"] = ""
                st.session_state["reg_password_input"] = ""
                st.session_state["reg_confirm_password_input"] = ""
                
                # Navigate back to login
                sleep(0.5)
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
    
    st.subheader("Admin Sign In")
    with st.form("admin_login_form", clear_on_submit=False):
        
        email = st.text_input("Admin Email ID", key="admin_login_email_input").lower()
        password = st.text_input("Password", type="password", key="admin_login_password_input")
        
        submitted = st.form_submit_button("Admin Sign In →", type="primary")
        
        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
                return

            user_data = get_admin_by_email(conn, email)

            if user_data:
                stored_hash = user_data.get('password_hash', '')
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
                    
                    # Redirect to the admin dashboard entry point in the main app
                    sleep(0.5)
                    set_auth_view('admin_dashboard_home') 
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

def render_admin_dashboard_home_view():
    """
    The main hub for the logged-in administrator.
    This function redirects the Admin to the 'visitor_dashboard' page 
    of the main application state.
    """
    # Enforce login
    if not st.session_state.get('admin_logged_in'):
        st.warning("Please log in to view the dashboard.")
        set_auth_view('admin_login')
        return

    # Set the main app's page control state to 'visitor_dashboard'
    st.session_state['current_page'] = 'visitor_dashboard'
    
    company_name = st.session_state.get('company_name', 'Your Company')
    admin_name = st.session_state.get('admin_name', 'Admin')
    
    # Display message before redirecting
    st.markdown(f"## 📊 {company_name} - Admin Hub")
    st.info(f"Welcome, **{admin_name}**. Navigating to Visitor Dashboard...")
    
    # Set the auth view to a non-interactive state and force re-run for main app to switch pages
    st.session_state['visitor_auth_view'] = 'admin_dashboard_home_redirected'
    st.rerun()

def render_forgot_password_view():
    """
    Renders the simplified TWO-STEP password reset flow (Insecure, but functional for demo).
    """
    st.warning("⚠️ **ADMIN OVERRIDE:** This simplified two-step flow allows direct password reset by only verifying the email's existence in the database. This is **HIGHLY INSECURE** for a real application and should be replaced with a secure email verification link system.")
    
    conn = get_fast_connection()

    # --- STAGE 1: EMAIL VERIFICATION ---
    if 'reset_user_id' not in st.session_state or st.session_state['reset_user_id'] is None:
        st.subheader("1. Verify Admin Email ID")
        with st.form("forgot_pass_verify_form", clear_on_submit=False):
            email_to_check = st.text_input("Enter your Admin Email ID", key="forgot_email_input").lower()
            submitted = st.form_submit_button("Check Email Existence", type="primary")

            if submitted:
                if not email_to_check:
                    st.error("Please enter an email address for lookup.")
                    return
                
                user_data = get_admin_by_email(conn, email_to_check)
                
                if user_data:
                    st.session_state['reset_user_id'] = user_data['id']
                    st.success("✅ Email ID verified! Proceed to set your new password.")
                    st.rerun() 
                else:
                    st.error("Email ID not found in our records.")
    
    # --- STAGE 2: PASSWORD RESET ---
    if st.session_state.get('reset_user_id') is not None:
        st.subheader("2. Set New Password")
        user_id_to_reset = st.session_state['reset_user_id']

        with st.form("forgot_pass_reset_form", clear_on_submit=True):
            new_password = st.text_input(f"New Password (min {MIN_PASSWORD_LENGTH} chars)", type="password", key="reset_new_password_input")
            confirm_password = st.text_input("Confirm New Password", type="password", key="reset_confirm_password_input")
            
            submitted = st.form_submit_button("Finalize Password Reset", type="primary")
            
            if submitted:
                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                    return
                elif len(new_password) < MIN_PASSWORD_LENGTH:
                    st.error(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
                    return

                new_hash = hash_password(new_password)

                if update_admin_password_directly(conn, user_id_to_reset, new_hash):
                    st.success("Password successfully changed! Redirecting to login...")
                    # Clear state and redirect
                    del st.session_state['reset_user_id']
                    sleep(0.5)
                    set_auth_view('admin_login')
                else:
                    st.error("Password reset failed due to a database error. Please check logs.")
            
    st.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)
    # The back button needs to clear the reset state if we are in step 2
    if st.button("← Back to Admin Login", key="forgot_back_login_btn", use_container_width=True):
        if 'reset_user_id' in st.session_state:
            del st.session_state['reset_user_id']
        set_auth_view('admin_login')


# ==============================================================================
# 5. MAIN APPLICATION ENTRY POINT
# ==============================================================================

def render_visitor_login_page():
    """
    Primary function to render the Admin Authentication page.
    Handles dynamic header titles and routes to the appropriate sub-view.
    """
    # --- Default view is 'admin_login' ---
    if 'visitor_auth_view' not in st.session_state:
        st.session_state['visitor_auth_view'] = 'admin_login'

    view = st.session_state['visitor_auth_view']
    
    # Determine Header Title based on current view
    header_titles = {
        'admin_register': "VISITOR MANAGEMENT - ADMIN REGISTRATION",
        'admin_login': "VISITOR MANAGEMENT - ADMIN LOGIN",
        'admin_dashboard_home': "VISITOR MANAGEMENT - DASHBOARD (REDIRECTING)",
        'admin_dashboard_home_redirected': "VISITOR MANAGEMENT - DASHBOARD (REDIRECTED)",
        'forgot_password': "VISITOR MANAGEMENT - RESET PASSWORD"
    }
    header_title = header_titles.get(view, "ADMIN AUTHENTICATION")
        
    # 1. Inject Custom CSS for styling
    st.markdown(f"""
    <style>
    /* CSS variables for consistency */
    :root {{
        --header-gradient: {HEADER_GRADIENT};
        --secondary-color: #7A42FF;
        --header-box-shadow: 0 4px 10px rgba(80, 48, 157, 0.4);
        --app-bg-color: #f7f9fc;
        --main-content-padding: 2.5rem; /* Padding for the main content area */
    }}

    /* GLOBAL STREAMLIT OVERRIDES */
    .stApp {{ background-color: var(--app-bg-color); }}
    .stApp > header {{ visibility: hidden; }}
    /* Important: Remove Streamlit's default container padding for the whole app */
    .stApp .main .block-container, 
    .css-18e3th9 {{ 
        padding: 0 !important; 
        max-width: 100% !important; 
        margin: 0 !important;
    }}
    .stApp .main {{ padding-top: 0 !important; margin-top: 0 !important; }}
    
    /* Header Box - Designed to look seamless with full-width top */
    .header-box {{
        background: var(--header-gradient);
        padding: 20px var(--main-content-padding);
        margin-top: 0px; 
        margin-bottom: 40px;
        border-radius: 0 0 15px 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        color: #FFFFFF;
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
    }}
    
    /* MAIN CONTENT WRAPPER for consistent padding on all views */
    .main-content-wrapper {{
        padding: 0 var(--main-content-padding);
    }}
    
    /* Form and Input Styling */
    .stTextInput input, .stTextArea textarea, .stSelectbox > div:first-child {{
        font-family: 'Inter', sans-serif;
        background-color: #ffffff; /* Brighter background */
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px 15px;
        font-size: 16px;
    }}
    .stTextInput label, .stTextArea label, .stSelectbox label {{
        font-weight: 600; /* Bolder labels */
        color: #333;
    }}
    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox > div:first-child:focus {{
        border-color: var(--secondary-color);
        box-shadow: 0 0 0 2px rgba(122, 66, 255, 0.4);
        outline: none;
    }}
    
    /* Primary Button Style (Gradient) */
    .stForm button[kind="primary"],
    /* Targeted primary style for non-form buttons like 'Check Email Existence' */
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
        border-radius: 8px !important;
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
    
    # 3. Dynamic View Rendering inside a controlled container
    st.markdown('<div class="main-content-wrapper">', unsafe_allow_html=True)

    if view == 'admin_register':
        render_admin_register_view()
    elif view == 'admin_login':
        render_existing_admin_login_view()
    elif view == 'admin_dashboard_home':
        render_admin_dashboard_home_view()
    elif view == 'admin_dashboard_home_redirected':
        # Non-interactive view state used after redirecting
        pass 
    elif view == 'forgot_password':
        render_forgot_password_view()
    
    st.markdown('</div>', unsafe_allow_html=True)
        
if __name__ == '__main__':
    render_visitor_login_page()
