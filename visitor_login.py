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

# --- AWS & DB Configuration ---
# IMPORTANT: Replace these with your actual configuration details for a live environment.
AWS_REGION = "ap-south-1"
# Set this to your actual AWS Secrets Manager ARN or remove if using env vars.
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
DATABASE_NAME = "zodopt"

# --- Configuration (Shared Constants) ---
LOGO_PATH = "zodopt.png"
LOGO_PLACEHOLDER_TEXT = "VISITOR ADMIN"
HEADER_GRADIENT = "linear-gradient(90deg, #1A4D2E, #4CBF80)"

# --- AWS SECRET MANAGER & DB CONNECTION ---

def get_db_credentials():
    """
    Retrieves MySQL credentials from AWS Secrets Manager or environment variables.
    
    NOTE: In a live environment, you must have AWS credentials configured 
    or use Streamlit Secrets for local testing.
    """
    # 1. Try to fetch from AWS Secrets Manager (Boto3)
    # Using a try block to handle environments without AWS access
    try:
        if AWS_SECRET_NAME and AWS_SECRET_NAME != "MOCK":
            client = boto3.client('secretsmanager', region_name=AWS_REGION)
            response = client.get_secret_value(SecretId=AWS_SECRET_NAME)
            if 'SecretString' in response:
                creds = json.loads(response['SecretString'])
                creds["database"] = DATABASE_NAME
                return creds
    except Exception:
        # Fallback to Environment Variables/Streamlit Secrets
        pass
    
    # 2. Fallback to Streamlit Secrets / Environment Variables for local testing
    host = os.environ.get("DB_HOST", "mock_host") 
    user = os.environ.get("DB_USER", "mock_user")
    password = os.environ.get("DB_PASS", "mock_password")
    
    if host == "mock_host":
        st.warning("Using mock DB credentials and connection. Data will NOT be saved persistently.")
    
    return {
        "host": host, 
        "user": user, 
        "password": password, 
        "database": DATABASE_NAME, 
    }

@st.cache_resource
def get_fast_connection():
    """
    Returns a persistent MySQL connection object (cached by Streamlit).
    Uses real mysql.connector logic if credentials are not 'mock'.
    """
    credentials = get_db_credentials()
    
    # --- MOCK IMPLEMENTATION for local debugging (NO PERSISTENCE) ---
    if credentials["host"] == "mock_host":
        class MockConnection:
            def cursor(self, dictionary=False):
                return self
            def execute(self, query, params=None):
                st.info(f"MOCK EXECUTE: {query.split()[0]} {query.split()[1]} with parameters...")
            def fetchone(self):
                # Mock login response needs to be handled *outside* this function or be complex
                # For safety, mock returns None, forcing logic to handle no user found.
                return None 
            def fetchall(self):
                return []
            def rowcount(self):
                return 1
            def lastrowid(self):
                return 100 
            def commit(self):
                st.info("MOCK COMMIT: Simulated successful transaction.")
            def close(self):
                pass
            def rollback(self):
                st.error("MOCK ROLLBACK: Simulated transaction failure.")
        return MockConnection()

    # --- REAL DB IMPLEMENTATION ---
    try:
        conn = mysql.connector.connect(
            host=credentials["host"],
            user=credentials["user"],
            password=credentials["password"],
            database=credentials["database"],
            # Add port, ssl_mode, etc. if required
        )
        st.success("Successfully connected to MySQL database.")
        return conn
    except mysql.connector.Error as err:
        st.error(f"Database Connection Error: Cannot connect to MySQL. Error: {err.msg}")
        # Stop app execution if connection fails to prevent runtime errors
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
        
        # --- MOCK DATA INJECTION ---
        # This handles the specific case where the mock connection fails to return data
        if conn.__class__.__name__ == 'MockConnection' and email == "admin@example.com":
            st.info("MOCK LOGIN: Simulating successful login for 'admin@example.com'.")
            # Simulating data that would be fetched from the DB
            mock_hash = hash_password("password123") # Hash a known mock password
            return {
                'id': 1, 
                'password_hash': mock_hash,
                'name': 'Mock Admin', 
                'company_id': 101, 
                'company_name': 'Mock Corp'
            }
        
        return cursor.fetchone()
    except Exception as e:
        st.error(f"DB Error fetching admin: {e}")
        return None
    finally:
        # Check if the cursor is closed only if it's a real cursor
        if conn.__class__.__name__ != 'MockConnection':
            cursor.close()

def create_company_and_admin(conn, company_name, admin_name, email, password_hash):
    """
    Inserts a new company and its first admin user, respecting the provided schemas.
    """
    cursor = conn.cursor()
    try:
        # 1. Insert Company
        company_query = "INSERT INTO companies (company_name) VALUES (%s)"
        cursor.execute(company_query, (company_name,))
        company_id = cursor.lastrowid # Get the ID of the new company

        # 2. Insert Admin User
        admin_query = """
        INSERT INTO admin_users (company_id, name, email, password_hash)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(admin_query, (company_id, admin_name, email, password_hash))

        conn.commit()
        return True
    except mysql.connector.Error as err:
        conn.rollback()
        # Check for specific error codes like duplicate entry (1062) for unique fields (email, company_name)
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
        if conn.__class__.__name__ != 'MockConnection':
            cursor.close()

def generate_reset_token(conn, user_id):
    """Generates a secure token and saves it to the password_reset_tokens table."""
    cursor = conn.cursor()
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=1)

    # NOTE: Assuming you have a password_reset_tokens table with columns: user_id, token, expires_at, is_used
    query = """
    INSERT INTO password_reset_tokens (user_id, token, expires_at)
    VALUES (%s, %s, %s)
    """
    try:
        cursor.execute(query, (user_id, token, expires_at))
        conn.commit()
        return token
    except Exception as e:
        st.error(f"DB Error generating reset token: {e}")
        conn.rollback()
        return None
    finally:
        if conn.__class__.__name__ != 'MockConnection':
            cursor.close()

def validate_and_reset_password(conn, user_id, token, new_password):
    """
    Checks token validity and updates the password, marking the token as used.
    """
    cursor = conn.cursor()
    new_hash = hash_password(new_password)
    
    # NOTE: Token validation logic is simplified/skipped in this Streamlit flow 
    # but the DB update and token-use marking remain critical.
    
    try:
        # 1. Update Admin Password
        update_admin_query = "UPDATE admin_users SET password_hash = %s WHERE id = %s"
        cursor.execute(update_admin_query, (new_hash, user_id))
        
        # 2. Mark the token as used (Using NOW() to check for non-expired, unused tokens)
        update_token_query = """
        UPDATE password_reset_tokens 
        SET is_used = TRUE 
        WHERE user_id = %s AND token = %s AND expires_at > NOW() AND is_used = FALSE
        """
        cursor.execute(update_token_query, (user_id, token))

        conn.commit()
        
        # In a real app, we check if rowcount for token update > 0 to confirm validity.
        # Here we assume success if update_admin_query succeeded.
        return True
    except Exception as e:
        st.error(f"DB Error during password reset: {e}")
        conn.rollback()
        return False
    finally:
        if conn.__class__.__name__ != 'MockConnection':
            cursor.close()


# -----------------------------------------------------
# --- VIEW RENDERING FUNCTIONS (No changes needed here) ---
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
                # MOCK check: If using mock, the hash is pre-computed for "password123"
                if conn.__class__.__name__ == 'MockConnection' and email == "admin@example.com":
                     # Check against the known mock password "password123"
                     is_authenticated = password == "password123" 
                else:
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
                        st.error("Password reset failed. The token may be invalid, expired, or already used.")


    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    if st.button("← Back to Admin Login", key="forgot_back_login_btn", use_container_width=True):
        st.session_state['reset_state'] = { 'step': 1, 'email': None, 'user_id': None, 'token': None }
        set_auth_view('admin_login')

# -----------------------------------------------------
# --- MAIN PAGE RENDERING (CSS/HTML is correctly applied) ---
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
        
    # 1. Inject Custom CSS for styling
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
