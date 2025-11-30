import streamlit as st
import os
import base64
import mysql.connector
import bcrypt 
import boto3 
import json 
import traceback 
from time import sleep

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
    (Placeholder: Real implementation required)
    """
    # Placeholder implementation
    st.error("Placeholder: DB credentials function needs real implementation.")
    # In a real application, you would use boto3.client('secretsmanager') here
    st.stop()

@st.cache_resource
def get_fast_connection():
    """
    Returns a persistent MySQL connection object (cached by Streamlit).
    (Placeholder: Real connection required)
    """
    try:
        # Replace this with the actual connection logic using mysql.connector
        # conn = mysql.connector.connect(...)
        return "MOCK_DB_CONNECTION" 
    except Exception as e:
        st.error(f"Database Connection Error: Cannot connect to MySQL. Ensure credentials are set. {e}")
        st.stop()


# --- Security Helper Functions ---
def hash_password(password):
    """Hashes a plaintext password using bcrypt."""
    # Using bcrypt to hash the new password before storing it
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
        # NOTE: Using a placeholder path for now as 'zodopt.png' might not exist in the environment
        # Replace this with actual path handling if deployed
        return "" 
    except Exception:
        return ""

# --- State Management Helper ---
def set_auth_view(view):
    """Changes the current view and forces a re-render."""
    st.session_state['visitor_auth_view'] = view
    # Using time.sleep(0.1) to ensure the rerun happens cleanly
    sleep(0.1) 
    st.rerun()

# -----------------------------------------------------
# --- PLACEHOLDER DB INTERACTION FUNCTIONS ---
# -----------------------------------------------------

def check_admin_exists_by_email(conn, email):
    """
    Placeholder: Checks the admin_users table for the email.
    If found, returns the user ID.
    """
    # --- ACTUAL DB QUERY ---
    # In a real app: SELECT id FROM admin_users WHERE email = %s
    # Mock behavior: only 'test@example.com' exists
    if email == "test@example.com":
        st.info("DB Mock: Admin user found (ID: 99).")
        return 99 # Mock user ID
    return None

def update_admin_password(conn, user_id, new_password):
    """
    Placeholder: Updates the password_hash in the admin_users table.
    """
    new_hash = hash_password(new_password)
    
    # --- ACTUAL DB UPDATE ---
    # In a real app: 
    # 1. UPDATE admin_users SET password_hash = %s WHERE id = %s
    # 2. UPDATE password_reset_tokens SET is_used = TRUE WHERE user_id = %s AND token = %s
    
    # Mock behavior: simulate success
    st.info(f"DB Mock: Updating user {user_id} with new password hash.")
    return True # Return success


# -----------------------------------------------------
# --- VIEW RENDERING FUNCTIONS ---
# -----------------------------------------------------

def render_admin_register_view():
    """Renders the form for registering a new Company and its initial Admin user."""
    # conn = get_fast_connection() # Use actual connection in production
    conn = None # Mocking connection for structural clarity

    st.markdown("### Register Your Company & Admin Account")
    
    with st.form("admin_register_form"):
        # --- Company & Admin Details ---
        st.markdown("**Company and Admin Details**")
        
        company_name = st.text_input("Company Name", key="reg_company_name")
        admin_name = st.text_input("Admin Full Name", key="reg_admin_name")
        admin_email = st.text_input("Email ID (Used for Login)", key="reg_admin_email")
        
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

            # --- Mock/Simulated DB Interaction ---
            # --- Actual DB Logic (Commented out, requires real connection) ---
            # 1. Hash the password: hashed_pass = hash_password(password)
            # 2. Insert Company: INSERT INTO companies (company_name) VALUES (%s)
            # 3. Get new company_id
            # 4. Insert Admin User: INSERT INTO admin_users (company_id, name, email, password_hash) VALUES (%s, %s, %s, %s)
            
            st.success(f"Company '{company_name}' and Admin '{admin_name}' successfully registered!")
            st.info("You can now sign in using your Email ID.")
            set_auth_view('admin_login') 
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
    # conn = get_fast_connection() # Use actual connection in production
    conn = None # Mocking connection for structural clarity

    st.markdown("### Admin Access - Sign In")
    
    with st.form("admin_login_form"):
        email = st.text_input("Admin Email ID", key="admin_login_email")
        password = st.text_input("Password", type="password", key="admin_login_password")
        
        submitted = st.form_submit_button("Admin Sign In →", type="primary")
        
        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
                return

            # --- Mock/Simulated DB Interaction ---
            # --- Actual DB Logic (Commented out, requires real connection) ---
            # 1. Query admin_users by email to get password_hash, company_id, name
            # 2. Verify password: if check_password(password, stored_hash):
            
            if email == "admin@zodopt.com" and password == "securepass":
                # Successful Login Simulation
                st.session_state['admin_logged_in'] = True
                st.session_state['admin_email'] = email
                st.session_state['admin_name'] = "System Admin"
                st.session_state['company_id'] = 1 
                st.session_state['company_name'] = "Zodopt Corp" 
                st.success(f"Welcome, {st.session_state['admin_name']}! Redirecting to dashboard...")
                
                # Navigate to the dashboard view
                set_auth_view('visitor_dashboard') 
                return
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
    
    st.info("This is the main dashboard area. In a complete application, this page would display real-time checked-in visitors and historical data.")

    # Dashboard Navigation - Check-in button is removed as requested
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
        for key in ['admin_logged_in', 'admin_email', 'admin_name', 'company_id', 'company_name']:
            if key in st.session_state:
                del st.session_state[key]
        set_auth_view('admin_login') # Redirect to the login page


def render_forgot_password_view():
    """
    Renders the password reset flow for admin users.
    Refined to simulate database interaction for user lookup and password update.
    """
    st.markdown("### Admin Password Reset")
    st.warning("Password reset requires a functional email service and database connection, which are currently simulated.")
    
    if 'reset_email' not in st.session_state:
        st.session_state['reset_email'] = None
        st.session_state['email_found'] = False
        st.session_state['reset_user_id'] = None # Store user ID after finding them
        
    conn = get_fast_connection() # Placeholder connection

    # --- Step 1: Check Email Existence ---
    if not st.session_state.email_found:
        with st.form("forgot_pass_email_form", clear_on_submit=False):
            email_to_check = st.text_input("Enter your registered Admin Email ID", key="forgot_email_input")
            
            if st.form_submit_button("Search Account", type="primary"):
                if not email_to_check:
                    st.warning("Please enter an email address.")
                    return
                
                # --- ACTUAL DB INTERACTION POINT (User Existence Check) ---
                user_id = check_admin_exists_by_email(conn, email_to_check)

                if user_id:
                    st.session_state['reset_email'] = email_to_check
                    st.session_state['reset_user_id'] = user_id
                    st.session_state['email_found'] = True
                    
                    # NOTE: In a real app, this is where you'd GENERATE the token (password_reset_tokens table), 
                    # send an email, and then wait for the user to click the link.
                    st.success("Account found. (Simulated: Please enter a new password below.)")
                    st.rerun() 
                else:
                    st.session_state['email_found'] = False
                    st.error("Email ID not found in our records.")

    # --- Step 2: Password Reset (If Email Found) ---
    if st.session_state.email_found:
        st.markdown("---")
        st.write(f"**Resetting password for:** `{st.session_state['reset_email']}` (User ID: {st.session_state['reset_user_id']})")
        with st.form("forgot_pass_reset_form"):
            new_password = st.text_input("New Password (min 8 chars)", type="password", key="reset_new_password")
            confirm_password = st.text_input("Confirm New Password", type="password", key="reset_confirm_password")
            
            if st.form_submit_button("Change Password", type="primary"):
                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    # --- ACTUAL DB INTERACTION POINT (Password Update) ---
                    user_id_to_update = st.session_state['reset_user_id']
                    
                    if update_admin_password(conn, user_id_to_update, new_password):
                        # NOTE: In a real app, you would also mark the reset token as used here.
                        st.success("Password successfully changed! You can now log in.")
                        
                        # Clean up state and redirect
                        st.session_state.email_found = False
                        st.session_state.reset_email = None
                        st.session_state.reset_user_id = None
                        set_auth_view('admin_login')
                    else:
                         st.error("Failed to update password in the database.")


    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    if st.button("← Back to Admin Login", key="forgot_back_login_btn", use_container_width=True):
        st.session_state.email_found = False
        st.session_state.reset_email = None
        st.session_state.reset_user_id = None
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
        
