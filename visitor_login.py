import streamlit as st
import os
import base64
import mysql.connector
import bcrypt 
import boto3 
import json 
import traceback 

# --- AWS & DB Configuration (Same as Conference App) ---
AWS_REGION = "ap-south-1" 
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS" 

# --- Configuration (Shared Constants) ---
LOGO_PATH = "zodopt.png" 
LOGO_PLACEHOLDER_TEXT = "VISITOR ADMIN"
HEADER_GRADIENT = "linear-gradient(90deg, #1A4D2E, #4CBF80)" # A new, distinct color for the admin portal

# --- AWS SECRET MANAGER & DB CONNECTION ---

# NOTE: For this demonstration, the actual connection logic is commented out and 
# replaced with placeholders. In a real environment, you must include the 
# implementation from the original conference_login.py file (or similar) here.
def get_db_credentials():
    # Placeholder implementation
    st.error("Placeholder: DB credentials function needs real implementation.")
    st.stop()

@st.cache_resource
def get_fast_connection():
    """
    Returns a persistent MySQL connection object (cached by Streamlit).
    In a real app, this should connect to MySQL using AWS Secrets Manager.
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
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""

# --- State Management Helper ---
def set_auth_view(view):
    """Changes the current view and forces a re-render."""
    st.session_state['visitor_auth_view'] = view
    st.rerun()

# -----------------------------------------------------
# --- VIEW RENDERING FUNCTIONS ---
# -----------------------------------------------------

def render_admin_register_view():
    """
    Renders the form for registering a new Company and its initial Admin user.
    """
    # conn = get_fast_connection() # Use actual connection in production
    conn = None # Mocking connection for structural clarity

    st.markdown("### Register Your Company & Admin Account")
    
    with st.form("admin_register_form"):
        # --- Company & Admin Details (Refined) ---
        st.markdown("**Company and Admin Details**")
        
        # User requested fields: Admin Name, Email ID, Company
        company_name = st.text_input("Company Name", key="reg_company_name")
        admin_name = st.text_input("Admin Full Name", key="reg_admin_name")
        admin_email = st.text_input("Email ID (Used for Login)", key="reg_admin_email")
        
        st.markdown("---")
        
        # Password Fields
        password = st.text_input("Password (min 8 chars)", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
        
        submitted = st.form_submit_button("Create Company & Admin Account", type="primary")
        
        if submitted:
            # Check if all required fields are filled (updated check)
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
            st.success(f"Company '{company_name}' and Admin '{admin_name}' successfully registered!")
            st.info("You can now sign in using your Email ID.")
            set_auth_view('admin_login') 
            return
            
            """
            # --- Actual DB Logic (Commented out, requires real connection) ---
            # NOTE: company_address removed from the insert query
            cursor = conn.cursor()
            try:
                # 1. Insert Company (Only company_name needed)
                company_query = "INSERT INTO companies (company_name) VALUES (%s)"
                cursor.execute(company_query, (company_name,))
                new_company_id = cursor.lastrowid # Get the newly created ID

                # 2. Insert Admin
                hashed_password = hash_password(password)
                admin_query = "INSERT INTO admin_users (company_id, name, email, password_hash) VALUES (%s, %s, %s, %s)"
                cursor.execute(admin_query, (new_company_id, admin_name, admin_email, hashed_password))
                
                conn.commit() # Commit the transaction
                st.success("Registration successful! Please sign in.")
                set_auth_view('admin_login')
            except mysql.connector.Error as err:
                conn.rollback() # Rollback on error
                if err.errno == 1062: # Duplicate entry for unique key (e.g., email or company name)
                     st.error("Registration failed. The Email ID or Company Name may already be in use.")
                else:
                    st.error(f"Database error during registration: {err}")
            finally:
                cursor.close()
            """
    
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
            if email == "admin@zodopt.com" and password == "securepass":
                # Successful Login Simulation
                st.session_state['admin_logged_in'] = True
                st.session_state['admin_email'] = email
                st.session_state['admin_name'] = "System Admin"
                st.session_state['company_id'] = 1 
                st.session_state['company_name'] = "Zodopt Corp" 
                st.success(f"Welcome, {st.session_state['admin_name']}! Logged in to {st.session_state['company_name']}.")
                set_auth_view('visitor_check_in')
                return
            else:
                st.error("Invalid Admin Email ID or Password.")
            
            """
            # --- Actual DB Logic (Commented out, requires real connection) ---
            cursor = conn.cursor(dictionary=True) 
            try:
                # Query joins admin_users and companies tables to fetch company_name
                query = "SELECT a.id, a.name, a.password_hash, a.company_id, c.company_name FROM admin_users a JOIN companies c ON a.company_id = c.id WHERE a.email = %s AND a.is_active = TRUE"
                cursor.execute(query, (email,))
                admin_record = cursor.fetchone()
                
                if admin_record and check_password(password, admin_record['password_hash']):
                    st.session_state['admin_logged_in'] = True
                    st.session_state['admin_email'] = email
                    st.session_state['admin_name'] = admin_record['name']
                    st.session_state['company_id'] = admin_record['company_id']
                    st.session_state['company_name'] = admin_record['company_name']
                    st.success(f"Welcome, {admin_record['name']}! Logged in to {admin_record['company_name']}.")
                    set_auth_view('visitor_check_in')
                else:
                    st.error("Invalid Admin Email ID or Password.")
            except mysql.connector.Error as err:
                st.error(f"Database error during login: {err}")
            finally:
                cursor.close()
            """
    
    # Navigation Buttons 
    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← New Registration", key="admin_new_reg_btn", use_container_width=True):
            set_auth_view('admin_register')
    with col2:
        if st.button("Forgot Password?", key="admin_forgot_pass_link", use_container_width=True):
            set_auth_view('forgot_password')

def render_visitor_check_in_view():
    """Renders the visitor check-in form and inserts data into the visitors table."""
    # Enforce login
    if not st.session_state.get('admin_logged_in'):
        st.warning("Please log in to check-in visitors.")
        set_auth_view('admin_login') # Redirect back to the login page
        return

    # conn = get_fast_connection() # Use actual connection in production
    conn = None # Mocking connection
    
    company_name = st.session_state.get('company_name', 'Your Company')
    company_id = st.session_state.get('company_id', 0)
    
    st.markdown(f"## 🏢 Visitor Check-in for {company_name}")
    st.markdown(f"Logged in as: **{st.session_state['admin_name']}**")
    st.markdown("---")

    with st.form("visitor_check_in_form"):
        col_name, col_phone = st.columns(2)
        with col_name:
            name = st.text_input("Visitor Name", key="visitor_name")
        with col_phone:
            phone = st.text_input("Phone Number", key="visitor_phone")
        
        visitor_company = st.text_input("Visitor's Company/Origin", key="visitor_company")
        reason = st.text_area("Reason for Visit/Host", key="visitor_reason")
        
        submitted = st.form_submit_button("Check-in Visitor", type="primary")

        if submitted:
            if not all([name, phone, visitor_company, reason]):
                st.error("Please fill in all visitor details.")
                return
            
            # --- Mock/Simulated DB Interaction ---
            st.success(f"✅ Visitor '{name}' successfully checked in to **{company_name}**.")
            
            """
            # --- Actual DB Logic (Commented out, requires real connection) ---
            cursor = conn.cursor()
            try:
                insert_query = ""
                INSERT INTO visitors (company_id, visitor_name, visitor_phone, visitor_company, reason_for_visit, check_in_time)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP())
                ""
                cursor.execute(insert_query, (company_id, name, phone, visitor_company, reason))
                st.success(f"✅ Visitor '{name}' successfully checked in to {company_name}!")
            except mysql.connector.Error as err:
                st.error(f"Database error during check-in: {err}")
            finally:
                cursor.close()
            """
    
    st.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)
    if st.button("← Logout", key="visitor_logout_btn", use_container_width=True):
        # Clear all admin session state
        for key in ['admin_logged_in', 'admin_email', 'admin_name', 'company_id', 'company_name']:
            if key in st.session_state:
                del st.session_state[key]
        set_auth_view('admin_login') # Redirect to the login page

def render_forgot_password_view():
    """Renders the password reset flow for admin users."""
    st.markdown("### Admin Password Reset")
    st.warning("Password reset requires a functional email service, which is simulated here.")
    
    # Initialize state variables for the two-step process
    if 'reset_email' not in st.session_state:
        st.session_state['reset_email'] = None
        st.session_state['email_found'] = False
        
    with st.form("forgot_pass_email_form", clear_on_submit=False):
        email_to_check = st.text_input("Enter your registered Admin Email ID", key="forgot_email_input", value=st.session_state.get('reset_email', ''))
        
        if st.form_submit_button("Search Account", type="primary"):
            if not email_to_check:
                st.warning("Please enter an email address.")
                return

            # --- Mock/Simulated DB Interaction ---
            if email_to_check.endswith("@zodopt.com"): # Simple mock check
                st.session_state['reset_email'] = email_to_check
                st.session_state['email_found'] = True
                st.success("Account found. (Simulated: Please enter a new password below.)")
                st.rerun() 
            else:
                st.session_state['email_found'] = False
                st.error("Email ID not found in our records.")
            
            """
            # --- Actual DB Logic (Commented out, requires real connection) ---
            # ... database check logic here ...
            """

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
                    # --- Mock/Simulated DB Interaction ---
                    st.success("Password successfully changed! You can now log in.")
                    
                    # Clear state and redirect to login
                    st.session_state.email_found = False
                    st.session_state.reset_email = None
                    set_auth_view('admin_login')
                    
                    """
                    # --- Actual DB Logic (Commented out, requires real connection) ---
                    # ... database update logic here ...
                    """


    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    if st.button("← Back to Admin Login", key="forgot_back_login_btn", use_container_width=True):
        st.session_state.email_found = False
        st.session_state.reset_email = None
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
    elif view == 'visitor_check_in':
        header_title = "VISITOR MANAGEMENT - CHECK-IN PORTAL"
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
    .stButton > button:not([key*="back_login_btn"]):not([key*="visitor_logout_btn"]):not([key*="existing_admin_login_btn"]) {{
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
    .stButton > button:not([key*="back_login_btn"]):not([key*="visitor_logout_btn"]):not([key*="existing_admin_login_btn"]):hover {{
        opacity: 0.9;
        transform: translateY(-2px);
    }}
    
    /* Secondary (Back/Login/Logout) Buttons */
    .stButton > button[key*="back_login_btn"],
    .stButton > button[key*="visitor_logout_btn"],
    .stButton > button[key*="existing_admin_login_btn"],
    .stButton > button[key*="admin_new_reg_btn"] {{
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
    elif view == 'visitor_check_in':
        render_visitor_check_in_view()
    elif view == 'forgot_password':
        render_forgot_password_view()
