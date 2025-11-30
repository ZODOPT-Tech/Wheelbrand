import streamlit as st
import os
import mysql.connector
import bcrypt
import boto3
import json
import traceback
from time import sleep
from datetime import datetime, timedelta # Used for token expiration logic
import secrets # Used for generating secure, random tokens

# --- AWS & DB Configuration (Same as Conference App) ---
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

# --- Configuration (Shared Constants) ---
LOGO_PATH = "zodopt.png"
LOGO_PLACEHOLDER_TEXT = "VISITOR ADMIN"
HEADER_GRADIENT = "linear-gradient(90deg, #1A4D2E, #4CBF80)" # A new, distinct color for the admin portal

# --- AWS SECRET MANAGER & DB CONNECTION ---

def get_db_credentials():
    """
    Retrieves MySQL credentials from AWS Secrets Manager.
    
    NOTE: In a real environment, this function would use boto3 to securely
    fetch credentials. Here, we use a placeholder for execution context.
    The 'database' key must be set to 'zodopt' or your desired database name.
    """
    try:
        # # --- REAL AWS IMPLEMENTATION (Requires Boto3 setup) ---
        # client = boto3.client('secretsmanager', region_name=AWS_REGION)
        # response = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        # if 'SecretString' in response:
        #     return json.loads(response['SecretString'])
        
        # --- MOCK IMPLEMENTATION (For running without real AWS/DB access) ---
        st.info("Using mock DB credentials and connection for demonstration.")
        return {
            "host": "mock_host", 
            "user": "mock_user", 
            "password": "mock_password", 
            "database": "zodopt", # Assuming the database name is 'zodopt'
        }
    except Exception as e:
        st.error(f"Error fetching DB credentials: {e}")
        st.stop()

@st.cache_resource
def get_fast_connection():
    """
    Returns a persistent MySQL connection object (cached by Streamlit).
    Uses actual mysql.connector logic with mock credentials.
    """
    credentials = get_db_credentials()
    if credentials["host"] == "mock_host":
        # Return a simple mock object if using mock credentials
        class MockConnection:
            def cursor(self):
                return self
            def execute(self, query, params=None):
                st.info(f"MOCK EXECUTE: {query} with {params}")
                # Simulate a successful execution for inserts/updates
                return 1 
            def fetchone(self):
                # Mock response for login/lookup. Must be handled by calling functions.
                return None 
            def lastrowid(self):
                # Simulate returning a new ID for the company/admin creation mock
                return 100 
            def commit(self):
                pass
            def close(self):
                pass
            def rollback(self):
                pass
        return MockConnection()

    try:
        conn = mysql.connector.connect(
            host=credentials["host"],
            user=credentials["user"],
            password=credentials["password"],
            database=credentials["database"],
            # port=3306, # Add port if needed
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Database Connection Error: Cannot connect to MySQL. Error: {err.msg}")
        st.stop()
    except Exception as e:
        st.error(f"Unexpected Connection Error: {e}")
        st.stop()


# --- Security Helper Functions ---
def hash_password(password):
    """Hashes a plaintext password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

def check_password(password, hashed_password):
    """Verifies a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

# --- Utility Function ---
def _get_image_base64(path):
    """Converts a local image file to a base64 string for embedding."""
    try:
        # NOTE: Placeholder path handler
        return "" 
    except Exception:
        return ""

# --- State Management Helper ---
def set_auth_view(view):
    """Changes the current view and forces a re-render."""
    st.session_state['visitor_auth_view'] = view
    sleep(0.1) 
    st.rerun()

# -----------------------------------------------------
# --- REAL DB INTERACTION FUNCTIONS ---
# -----------------------------------------------------

def get_admin_by_email(conn, email):
    """Fetches user ID, hash, name, and company details for login/lookup."""
    # Using dictionary=True to return results as dictionaries (easier access)
    cursor = conn.cursor(dictionary=True) 
    query = """
    SELECT au.id, au.password_hash, au.name, c.id AS company_id, c.company_name
    FROM admin_users au
    JOIN companies c ON au.company_id = c.id
    WHERE au.email = %s AND au.is_active = 1;
    """
    try:
        cursor.execute(query, (email,))
        return cursor.fetchone()
    except Exception as e:
        st.error(f"DB Error fetching admin: {e}")
        return None
    finally:
        cursor.close()

def create_company_and_admin(conn, company_name, admin_name, email, password_hash):
    """
    Inserts a new company and its first admin user, respecting the provided schemas.
    """
    cursor = conn.cursor()
    try:
        # 1. Insert Company (Only company_name, as per schema)
        company_query = "INSERT INTO companies (company_name) VALUES (%s)"
        cursor.execute(company_query, (company_name,))
        company_id = cursor.lastrowid # Get the ID of the new company

        # 2. Insert Admin User (Using name, email, password_hash, company_id, as per schema)
        admin_query = """
        INSERT INTO admin_users (company_id, name, email, password_hash)
        VALUES (%s, %s, %s, %s)
        """
        # is_active and created_at use their default values in the table definition.
        cursor.execute(admin_query, (company_id, admin_name, email, password_hash))

        conn.commit()
        return True
    except mysql.connector.Error as err:
        conn.rollback()
        # Check for specific error codes like duplicate entry (1062) for unique fields
        if err.errno == 1062:
             st.error("Registration failed: An account with this email or company name already exists.")
        else:
             st.error(f"Registration failed (DB error): {err.msg}")
        return False
    except Exception as e:
        conn.rollback()
        st.error(f"Registration failed (General error): {e}")
        return False
    finally:
        cursor.close()

def generate_reset_token(conn, user_id):
    """Generates a secure token and saves it to the password_reset_tokens table."""
    cursor = conn.cursor()
    token = secrets.token_urlsafe(32) # Generate a 32-byte secure, URL-safe token
    expires_at = datetime.now() + timedelta(hours=1) # Token expires in 1 hour

    query = """
    INSERT INTO password_reset_tokens (user_id, token, expires_at)
    VALUES (%s, %s, %s)
    """
    try:
        # Clear any existing unused tokens for this user first (optional, but good practice)
        # delete_query = "DELETE FROM password_reset_tokens WHERE user_id = %s AND is_used = FALSE AND expires_at > NOW()"
        # cursor.execute(delete_query, (user_id,))
        
        cursor.execute(query, (user_id, token, expires_at))
        conn.commit()
        return token
    except Exception as e:
        st.error(f"DB Error generating reset token: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()

def validate_and_reset_password(conn, user_id, token, new_password):
    """
    Checks token validity and updates the password, marking the token as used.
    NOTE: In a real app, the token would be passed via URL and validated here.
    For this Streamlit mock, we skip token validation but include the logic structure.
    """
    cursor = conn.cursor()
    new_hash = hash_password(new_password)
    
    # 1. Check if token is valid (not used, not expired) - SKIPPED IN MOCK FOR SIMPLICITY
    # In a real app, this query would check the token and expires_at
    
    try:
        # 2. Update Admin Password
        update_admin_query = "UPDATE admin_users SET password_hash = %s WHERE id = %s"
        cursor.execute(update_admin_query, (new_hash, user_id))
        
        # 3. Mark the token as used (Using MOCK token 'SIMULATED_TOKEN' in this context)
        # This prevents token reuse.
        update_token_query = """
        UPDATE password_reset_tokens 
        SET is_used = TRUE 
        WHERE user_id = %s AND token = %s AND expires_at > NOW() AND is_used = FALSE
        """
        # Since we don't have the real token from an email link, we use the one generated 
        # in the session state which simulates a successful validation.
        # This assumes the token provided here is the valid one.
        cursor.execute(update_token_query, (user_id, token))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"DB Error during password reset: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()


# -----------------------------------------------------
# --- VIEW RENDERING FUNCTIONS ---
# -----------------------------------------------------

def render_admin_register_view():
    """Renders the form for registering a new Company and its initial Admin user."""
    conn = get_fast_connection() 

    st.markdown("### Register Your Company & Admin Account")
    
    with st.form("admin_register_form"):
        # --- Company & Admin Details ---
        st.markdown("**Company and Admin Details**")
        
        company_name = st.text_input("Company Name", key="reg_company_name")
        admin_name = st.text_input("Admin Full Name", key="reg_admin_name")
        admin_email = st.text_input("Email ID (Used for Login)", key="reg_admin_email").lower()
        
        st.markdown("---")
        
        # Password Fields
        password = st.text_input("Password (min 8 chars)", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
        
        submitted = st.form_submit_button("Create Company & Admin Account", type="primary")
        
        if submitted:
            if not all([company_name, admin_name, admin_email, password, confirm_password]):
                st.error("Please fill in all required fields.")
                return
            elif password != confirm_password:
                st.error("Passwords do not match.")
                return
            elif len(password) < 8:
                st.error("Password must be at least 8 characters long.")
                return

            # --- DB Interaction ---
            hashed_pass = hash_password(password)
            
            if create_company_and_admin(conn, company_name, admin_name, admin_email, hashed_pass):
                st.success(f"Company '{company_name}' and Admin '{admin_name}' successfully registered!")
                st.info("You can now sign in using your Email ID.")
                set_auth_view('admin_login') 
            # Note: create_company_and_admin handles failure messages internally.
            return
    
    # Navigation Buttons 
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
    Redirects to 'visitor_dashboard' on success.
    """
    conn = get_fast_connection() 

    st.markdown("### Admin Access - Sign In")
    
    with st.form("admin_login_form"):
        email = st.text_input("Admin Email ID", key="admin_login_email").lower()
        password = st.text_input("Password", type="password", key="admin_login_password")
        
        submitted = st.form_submit_button("Admin Sign In →", type="primary")
        
        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
                return

            # --- DB Interaction ---
            user_data = get_admin_by_email(conn, email)

            if user_data:
                stored_hash = user_data['password_hash']
                if check_password(password, stored_hash):
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
    
    # Navigation Buttons 
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
    It will show current visitors, history, and navigation options.
    """
    # Enforce login
    if not st.session_state.get('admin_logged_in'):
        st.warning("Please log in to view the dashboard.")
        set_auth_view('admin_login')
        return

    company_name = st.session_state.get('company_name', 'Your Company')
    admin_name = st.session_state.get('admin_name', 'Admin')

    st.markdown(f"## 📊 {company_name} - Admin Dashboard")
    st.markdown(f"Welcome back, **{admin_name}**.")
    st.markdown("---")
    
    st.info(f"You are logged in as Admin ID: **{st.session_state['admin_id']}** at **{company_name}** (Company ID: {st.session_state['company_id']}).")

    # Dashboard Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👥 View Visitor History", key="dash_view_history_btn", use_container_width=True, type="primary"):
            st.warning("Feature not yet implemented. This would show the list of visitors.")
    with col2:
        if st.button("⚙️ Admin Settings", key="dash_admin_settings_btn", use_container_width=True):
            st.warning("Feature not yet implemented.")

    st.markdown('<div style="margin-top: 35px;"></div>', unsafe_allow_html=True)
    if st.button("← Logout", key="dashboard_logout_btn", use_container_width=True):
        # Clear all admin session state
        for key in ['admin_logged_in', 'admin_id', 'admin_email', 'admin_name', 'company_id', 'company_name']:
            if key in st.session_state:
                del st.session_state[key]
        set_auth_view('admin_login') # Redirect to the login page


def render_forgot_password_view():
    """
    Renders the password reset flow for admin users, simulating token generation/update.
    """
    st.markdown("### Admin Password Reset")
    st.warning("Password reset requires a functional email service and database connection, which are currently simulated.")
    
    # State management for the reset flow
    if 'reset_state' not in st.session_state:
        st.session_state['reset_state'] = {
            'step': 1, # 1: Email check, 2: Token verification/password reset
            'email': None,
            'user_id': None,
            'token': None # The simulated token
        }
    
    state = st.session_state['reset_state']
    conn = get_fast_connection()

    # --- Step 1: Check Email Existence & Generate Token ---
    if state['step'] == 1:
        with st.form("forgot_pass_email_form", clear_on_submit=False):
            email_to_check = st.text_input("Enter your registered Admin Email ID", key="forgot_email_input").lower()
            
            if st.form_submit_button("Request Password Reset Link", type="primary"):
                if not email_to_check:
                    st.warning("Please enter an email address.")
                    return
                
                user_data = get_admin_by_email(conn, email_to_check)

                if user_data:
                    user_id = user_data['id']
                    
                    # --- ACTUAL DB INTERACTION POINT (Generate Token) ---
                    # The generated token is the secret key sent via email
                    reset_token = generate_reset_token(conn, user_id)

                    if reset_token:
                        state['email'] = email_to_check
                        state['user_id'] = user_id
                        state['token'] = reset_token # Store the generated token
                        state['step'] = 2
                        
                        st.success("A password reset link has been (simulated) sent to your email.")
                        st.info(f"**MOCK TOKEN:** `{reset_token}`. In a real app, you would click the link containing this token to proceed.")
                        st.rerun() 
                    else:
                        st.error("Failed to generate a reset token. Please try again.")
                else:
                    st.error("Email ID not found in our records.")

    # --- Step 2: Password Reset (Simulating token arrival via email link) ---
    elif state['step'] == 2:
        st.markdown("---")
        st.write(f"**Resetting password for:** `{state['email']}` (User ID: {state['user_id']})")
        
        # In a real app, this token would be prepopulated from a query string (URL parameter)
        # We are using the stored token for this mock.
        reset_token_input = st.text_input("Enter Reset Token (Simulated Link)", value=state['token'], key="reset_token_input", disabled=True)
        
        with st.form("forgot_pass_reset_form"):
            new_password = st.text_input("New Password (min 8 chars)", type="password", key="reset_new_password")
            confirm_password = st.text_input("Confirm New Password", type="password", key="reset_confirm_password")
            
            if st.form_submit_button("Change Password", type="primary"):
                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    # --- ACTUAL DB INTERACTION POINT (Validate Token & Update Password) ---
                    if validate_and_reset_password(conn, state['user_id'], reset_token_input, new_password):
                        st.success("Password successfully changed! You can now log in.")
                        
                        # Clean up state and redirect
                        st.session_state['reset_state'] = { 'step': 1, 'email': None, 'user_id': None, 'token': None }
                        set_auth_view('admin_login')
                    else:
                        # This would catch DB errors or expired/invalid tokens in a real implementation
                        st.error("Password reset failed. The token may be invalid, expired, or already used.")


    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    if st.button("← Back to Admin Login", key="forgot_back_login_btn", use_container_width=True):
        st.session_state['reset_state'] = { 'step': 1, 'email': None, 'user_id': None, 'token': None }
        set_auth_view('admin_login')

# -----------------------------------------------------
# --- MAIN PAGE RENDERING ---
# -----------------------------------------------------

def render_visitor_login_page():
    # --- Default view is 'admin_login' ---
    if 'visitor_auth_view' not in st.session_state:
        st.session_state['visitor_auth_view'] = 'admin_login'

    # Determine the header title
    view = st.session_state['visitor_auth_view']
    if view == 'admin_register':
        header_title = "VISITOR MANAGEMENT - ADMIN REGISTRATION"
    elif view == 'admin_login':
        header_title = "VISITOR MANAGEMENT - ADMIN LOGIN"
    elif view == 'visitor_dashboard':
        header_title = "VISITOR MANAGEMENT - DASHBOARD" 
    elif view == 'forgot_password':
        header_title = "VISITOR MANAGEMENT - RESET PASSWORD"
        
    # 1. Inject Custom CSS for styling (CSS remains unchanged, only included for completeness)
    st.markdown(f"""
    <style>
    /* CSS variables for consistency */
    :root {{
        --header-gradient: {HEADER_GRADIENT};
        --primary-color: #1A4D2E;
        --secondary-color: #4CBF80;
        --header-box-shadow: 0 4px 10px rgba(26, 77, 46, 0.4);
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
        box-shadow: 0 0 0 2px rgba(76, 191, 128, 0.4);
        outline: none;
    }}
    
    /* Primary Button Style (Gradient) */
    .stForm button[kind="primary"],
    .stButton > button:not([key*="back_login_btn"]):not([key*="logout_btn"]):not([key*="existing_admin_login_btn"]):not([key*="checkin_back_dash_btn"]) {{
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
    .stButton > button:not([key*="back_login_btn"]):not([key*="logout_btn"]):not([key*="existing_admin_login_btn"]):not([key*="checkin_back_dash_btn"]):hover {{
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
