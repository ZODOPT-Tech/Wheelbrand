import streamlit as st
import os
import base64
import mysql.connector
import bcrypt # Used for secure password hashing
import boto3 # Used for AWS Secrets Manager
import json # Used for parsing secret string
import traceback # Used for detailed error logging

# --- AWS & DB Configuration ---
# IMPORTANT: Replace these with your actual AWS region and secret name
AWS_REGION = "ap-south-1" 
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS" 

# --- Configuration (Shared Constants) ---
# NOTE: Using a placeholder path for the logo. In a real environment, 
# you'd need to ensure this path is accessible or use a hosted URL.
LOGO_PATH = "images/zodopt.png" 
LOGO_PLACEHOLDER_TEXT = "zodopt"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)" # Primary Color for header and main buttons

# --- AWS SECRET MANAGER ----------------
@st.cache_resource
def get_db_credentials():
    """
    Loads DB credentials from AWS Secrets Manager.
    Secret must be a JSON string with keys:
    DB_HOST, DB_NAME, DB_USER, DB_PASSWORD
    """
    # 
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    try:
        # This function fetches the secret value. 
        # Ensure your AWS environment is configured with the necessary permissions.
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        # SecretsManager stores text in 'SecretString'
        if "SecretString" not in resp:
            raise RuntimeError("SecretString missing in AWS secrets response.")
        creds = json.loads(resp["SecretString"])
        required_keys = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        for k in required_keys:
            if k not in creds:
                raise RuntimeError(f"Missing key in secret: {k}")
        return creds
    except Exception as e:
        # Display a user-friendly error in Streamlit
        st.error(f"Configuration Error: Could not retrieve database credentials from AWS Secrets Manager. Details: {e}")
        # Log the full traceback for the developer in the console
        st.write(traceback.format_exc())
        st.stop()


# ---------------- FAST DB CONNECTION ----------------
@st.cache_resource
def get_fast_connection():
    """
    Returns a persistent MySQL connection object (cached by Streamlit).
    This function establishes the connection using credentials from Secrets Manager.
    """
    c = get_db_credentials()
    try:
        conn = mysql.connector.connect(
            host=c["DB_HOST"],
            user=c["DB_USER"],
            password=c["DB_PASSWORD"],
            database=c["DB_NAME"],
            port=3306,
            autocommit=True, # Ensure changes are saved immediately
            connection_timeout=10,
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"Database Connection Error: Could not connect to MySQL. Please check credentials and network access. Details: {e}")
        st.stop()


# --- Security Helper Functions ---
def hash_password(password):
    """Hashes a plaintext password using bcrypt for secure storage."""
    # Generate a salt and hash the password
    # 12 is a secure default work factor
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

def check_password(password, hashed_password):
    """Verifies a plaintext password against a stored bcrypt hash."""
    try:
        # bcrypt.checkpw handles both hashing the input and comparing the result
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        # Handle cases where the hash might be malformed or password encoding fails
        return False

# --- Utility Function ---
def _get_image_base64(path):
    """Converts a local image file to a base64 string for embedding in HTML/CSS."""
    # This is necessary for embedding local images directly into Streamlit's markdown/HTML
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        # Returns an empty string if the file is not found, preventing errors
        return ""

# --- State Management Helper ---
def set_auth_view(view):
    """Changes the current authentication view (login, register, forgot_password) and forces a re-render."""
    st.session_state['conf_auth_view'] = view
    st.rerun()

# -----------------------------------------------------
# --- VIEW RENDERING FUNCTIONS (DB INTEGRATED) ---
# -----------------------------------------------------

def render_login_view():
    """Renders the standard login form and handles DB authentication."""
    conn = get_fast_connection()
    
    st.subheader("Sign In")
    with st.form("conf_login_form"):
        email = st.text_input("Email ID", key="conf_login_email")
        password = st.text_input("Password", type="password", key="conf_login_password")
        
        submitted = st.form_submit_button("Sign In →", type="primary")
        
        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
                return

            cursor = conn.cursor(dictionary=True) # Use dictionary=True to get results as dicts
            try:
                # 1. Look up user by email in the conference_users table
                query = "SELECT id, name, password_hash FROM conference_users WHERE email = %s AND is_active = TRUE"
                cursor.execute(query, (email,))
                user_record = cursor.fetchone()
                
                if user_record and check_password(password, user_record['password_hash']):
                    # 2. Login successful: Set session state for the user
                    st.success(f"Welcome, {user_record['name']}! Logged in successfully.")
                    st.session_state['logged_in'] = True
                    st.session_state['user_id'] = user_record['id']
                    st.session_state['user_email'] = email
                    st.session_state['user_name'] = user_record['name']
                    # Redirect to the main dashboard or app page
                    st.session_state['current_page'] = 'conference_dashboard' 
                    st.rerun()
                else:
                    # 3. Login failed 
                    st.error("Invalid Email ID or Password.")
            except mysql.connector.Error as err:
                st.error(f"Database error during login: {err}")
            finally:
                cursor.close()
    
    # Navigation Buttons 
    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Registration", key="conf_new_reg_btn", use_container_width=True):
            set_auth_view('register')
    with col2:
        if st.button("Forgot Password?", key="conf_forgot_pass_btn", use_container_width=True):
            set_auth_view('forgot_password')

def render_register_view():
    """Renders the new delegate registration form and inserts user into DB."""
    conn = get_fast_connection()

    st.subheader("New Delegate Registration")
    with st.form("conf_register_form"):
        name = st.text_input("Name", key="reg_name")
        email = st.text_input("Email ID", key="reg_email")
        company = st.text_input("Company", key="reg_company")
        password = st.text_input("Password (min 8 chars)", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
        
        submitted = st.form_submit_button("Register Account", type="primary")

        if submitted:
            if not all([name, email, company, password, confirm_password]):
                st.error("Please fill in all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters long.")
            else:
                cursor = conn.cursor()
                try:
                    # 1. Check if Email ID is already registered (unique constraint check)
                    check_query = "SELECT COUNT(*) FROM conference_users WHERE email = %s"
                    cursor.execute(check_query, (email,))
                    if cursor.fetchone()[0] > 0:
                        st.error("This Email ID is already registered. Please try logging in.")
                        return

                    # 2. Hash the password securely
                    hashed_password = hash_password(password)

                    # 3. Insert new user into the database
                    insert_query = """
                    INSERT INTO conference_users (name, email, company, password_hash)
                    VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (name, email, company, hashed_password))
                    
                    st.success("Registration successful! You can now sign in.")
                    set_auth_view('login')
                except mysql.connector.Error as err:
                    st.error(f"Database error during registration: {err}")
                finally:
                    cursor.close()
    
    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    if st.button("← Back to Login", key="reg_back_login_btn", use_container_width=True):
        set_auth_view('login')

def render_forgot_password_view():
    """
    Renders the password reset flow. 
    NOTE: This implementation focuses on the Streamlit UI and DB update.
    The complex parts (token generation, email sending, token verification from the
    'conference_reset_password' table) are simulated.
    """
    conn = get_fast_connection()
    
    # Initialize state variables for the two-step process
    if 'reset_email' not in st.session_state:
        st.session_state['reset_email'] = None
        st.session_state['email_found'] = False
        
    st.subheader("Reset Password")
    
    # --- Step 1: Email Input (Simulate Account Search) ---
    with st.form("forgot_pass_email_form", clear_on_submit=False):
        email_to_check = st.text_input("Enter your registered Email ID", key="forgot_email_input", value=st.session_state.get('reset_email', ''))
        
        if st.form_submit_button("Search Account", type="primary"):
            if not email_to_check:
                st.warning("Please enter an email address.")
                return

            cursor = conn.cursor()
            try:
                # Check if email exists to proceed
                check_query = "SELECT id FROM conference_users WHERE email = %s"
                cursor.execute(check_query, (email_to_check,))
                user_id = cursor.fetchone()

                if user_id:
                    st.session_state['reset_email'] = email_to_check
                    st.session_state['email_found'] = True
                    st.success("Account found. (In a production app, a secure reset link would be sent to this email.) Please enter a new password below.")
                    st.rerun() 
                else:
                    st.session_state['email_found'] = False
                    st.error("Email ID not found in our records.")
            except mysql.connector.Error as err:
                st.error(f"Database error during email check: {err}")
            finally:
                cursor.close()

    # --- Step 2: Password Reset (If Email Found) ---
    if st.session_state.email_found:
        st.markdown("---")
        st.write(f"**Resetting password for:** `{st.session_state['reset_email']}`")
        with st.form("forgot_pass_reset_form"):
            new_password = st.text_input("New Password (min 8 chars)", type="password", key="reset_new_password")
            confirm_password = st.text_input("Confirm New Password", type="password", key="reset_confirm_password")
            
            if st.form_submit_button("Change Password", type="primary"):
                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    # In a real app, this update would only happen after token validation.
                    cursor = conn.cursor()
                    try:
                        new_hashed_password = hash_password(new_password)
                        
                        update_query = "UPDATE conference_users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE email = %s"
                        cursor.execute(update_query, (new_hashed_password, st.session_state['reset_email']))
                        
                        st.success("Password successfully changed! You can now log in.")
                        
                        # Clear state and redirect to login
                        st.session_state.email_found = False
                        st.session_state.reset_email = None
                        set_auth_view('login')
                    except mysql.connector.Error as err:
                        st.error(f"Database error during password change: {err}")
                    finally:
                        cursor.close()

    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    if st.button("← Back to Login", key="forgot_back_login_btn", use_container_width=True):
        st.session_state.email_found = False
        st.session_state.reset_email = None
        set_auth_view('login')


# -----------------------------------------------------
# --- MAIN FUNCTION (Page Layout and Routing) ---
# -----------------------------------------------------

def render_conference_login_page():
    # Initialize the view state
    if 'conf_auth_view' not in st.session_state:
        st.session_state['conf_auth_view'] = 'login'

    # Determine the header title based on the current view state
    view = st.session_state['conf_auth_view']
    if view == 'login':
        header_title = "CONFERENCE BOOKING" 
    elif view == 'register':
        header_title = "NEW REGISTRATION"  
    elif view == 'forgot_password':
        header_title = "RESET PASSWORD"     
        
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
        border-radius: 0 0 15px 15px; /* Only round the bottom corners */
        box-shadow: 0 4px 15px rgba(0,0,0,0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
        /* Force full width in Streamlit's main content area */
        width: calc(100% + 4rem); 
        margin-left: -2rem; 
        margin-right: -2rem; 
    }}
    .header-title {{
        font-family: 'Inter', sans-serif; 
        font-size: 34px;
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
    .stTextInput input {{
        font-family: 'Inter', sans-serif;
        background-color: #f0f2f6;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px 15px;
        font-size: 16px;
    }}
    .stTextInput input:focus {{
        border-color: var(--secondary-color);
        box-shadow: 0 0 0 2px rgba(122, 66, 255, 0.4);
        outline: none;
    }}
    
    /* Primary Button Style (Used for all gradient buttons) */
    .stForm button[kind="primary"],
    .stButton > button:not([key*="back_login_btn"]):not([key*="conf_back_main_btn"]) {{
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
    .stButton > button:not([key*="back_login_btn"]):not([key*="conf_back_main_btn"]):hover {{
        opacity: 0.95;
        transform: translateY(-2px);
    }}
    
    /* Secondary (Back) Buttons */
    .stButton > button[key*="back_login_btn"],
    .stButton > button[key*="conf_back_main_btn"] {{
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
    .stButton > button[key*="back_login_btn"]:hover,
    .stButton > button[key*="conf_back_main_btn"]:hover {{
        background: #F0F2F6 !important;
    }}
    </style>
    """, unsafe_allow_html=True)


    # 2. HEADER (Dynamic Title & Logo)
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

    # 3. Dynamic View Rendering (The central logic)
    # The content is centered automatically by Streamlit's default layout
    if view == 'login':
        render_login_view()
    elif view == 'register':
        render_register_view()
    elif view == 'forgot_password':
        render_forgot_password_view()
    
  
