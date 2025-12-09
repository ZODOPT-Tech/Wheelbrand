import streamlit as st
import os
import base64
import mysql.connector
import bcrypt
import boto3
import json
import traceback

# --- AWS & DB Configuration ---
AWS_REGION = "ap-south-1" 
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS" 

# --- Configuration (Shared Constants) ---
LOGO_PATH = "zodopt.png" 
LOGO_PLACEHOLDER_TEXT = "zodopt"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)" 

# --- AWS SECRET MANAGER ----------------
@st.cache_resource
def get_db_credentials():
    """Loads DB credentials from AWS Secrets Manager."""
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    try:
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        if "SecretString" not in resp:
            raise RuntimeError("SecretString missing in AWS secrets response.")
        creds = json.loads(resp["SecretString"])
        required_keys = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        for k in required_keys:
            if k not in creds:
                raise RuntimeError(f"Missing key in secret: {k}")
        return creds
    except Exception as e:
        st.error(f"Configuration Error: Could not retrieve database credentials from AWS Secrets Manager. Details: {e}")
        st.write(traceback.format_exc())
        st.stop()


# ---------------- FAST DB CONNECTION ----------------
@st.cache_resource
def get_fast_connection():
    """Returns a persistent MySQL connection object (cached by Streamlit)."""
    c = get_db_credentials()
    try:
        conn = mysql.connector.connect(
            host=c["DB_HOST"],
            user=c["DB_USER"],
            password=c["DB_PASSWORD"],
            database=c["DB_NAME"],
            port=3306,
            autocommit=True,
            connection_timeout=10,
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"Database Connection Error: Could not connect to MySQL. Please check credentials and network access. Details: {e}")
        st.stop()


# --- Security Helper Functions ---
def hash_password(password):
    """Hashes a plaintext password using bcrypt for secure storage."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

def check_password(password, hashed_password):
    """Verifies a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

# --- Utility Function ---
def _get_image_base64(path):
    """Converts a local image file to a base64 string for embedding in HTML/CSS."""
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""

# --- State Management Helper ---
def set_auth_view(view):
    """Changes the current authentication view and forces a re-render."""
    st.session_state['conf_auth_view'] = view
    st.rerun()

# -----------------------------------------------------
# --- VIEW RENDERING FUNCTIONS (DB INTEGRATED) ---
# -----------------------------------------------------

def render_login_view():
    """Renders the standard login form and handles DB authentication."""
    conn = get_fast_connection()
    
    # Start the form inside the card container
    with st.container(border=False):
        # We need a custom container to apply the card styling, as st.form doesn't accept the 'container' styling readily.
        st.markdown('<div class="auth-card-wrapper">', unsafe_allow_html=True)
        
        with st.form("conf_login_form"):
            st.markdown("### Sign In to Your Account")
            email = st.text_input("Email ID", key="conf_login_email")
            password = st.text_input("Password", type="password", key="conf_login_password")
            
            submitted = st.form_submit_button("Sign In →", type="primary")
            
            if submitted:
                if not email or not password:
                    st.error("Please enter both email and password.")
                    return

                cursor = conn.cursor(dictionary=True)
                try:
                    query = "SELECT id, name, password_hash FROM conference_users WHERE email = %s AND is_active = TRUE"
                    cursor.execute(query, (email,))
                    user_record = cursor.fetchone()
                    
                    if user_record and check_password(password, user_record['password_hash']):
                        st.success(f"Welcome, {user_record['name']}! Logged in successfully.")
                        st.session_state['logged_in'] = True
                        st.session_state['user_id'] = user_record['id']
                        st.session_state['user_email'] = email
                        st.session_state['user_name'] = user_record['name']
                        st.session_state['current_page'] = 'conference_dashboard' 
                        st.rerun()
                    else:
                        st.error("Invalid Email ID or Password.")
                except mysql.connector.Error as err:
                    st.error(f"Database error during login: {err}")
                finally:
                    cursor.close()

        st.markdown('</div>', unsafe_allow_html=True) # Close custom card container
    
    # Navigation Buttons (Outside the form and card)
    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Registration", key="conf_new_reg_btn", type="secondary", use_container_width=True):
            set_auth_view('register')
    with col2:
        if st.button("Forgot Password?", key="conf_forgot_pass_btn", type="secondary", use_container_width=True):
            set_auth_view('forgot_password')

def render_register_view():
    """Renders the new delegate registration form and inserts user into DB."""
    conn = get_fast_connection()

    DEPARTMENT_OPTIONS = [
        "SELECT", "SALES", "HR", "FINANCE", "DELIVERY/TECH", "DIGITAL MARKETING", "IT"
    ]
    
    with st.container(border=False):
        st.markdown('<div class="auth-card-wrapper">', unsafe_allow_html=True)
        
        with st.form("conf_register_form"):
            st.markdown("### Create New Account")
            name = st.text_input("Name", key="reg_name")
            email = st.text_input("Email ID", key="reg_email")
            company = st.text_input("Company", key="reg_company")
            
            department = st.selectbox(
                "Department", 
                options=DEPARTMENT_OPTIONS, 
                key="reg_department"
            )
            
            password = st.text_input("Password (min 8 chars)", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
            
            submitted = st.form_submit_button("Register Account", type="primary")

            if submitted:
                is_department_selected = department != "SELECT"
                
                if not all([name, email, company, password, confirm_password]):
                    st.error("Please fill in all fields.")
                elif not is_department_selected:
                    st.error("Please select a Department.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters long.")
                else:
                    cursor = conn.cursor()
                    try:
                        check_query = "SELECT COUNT(*) FROM conference_users WHERE email = %s"
                        cursor.execute(check_query, (email,))
                        if cursor.fetchone()[0] > 0:
                            st.error("This Email ID is already registered. Please try logging in.")
                            return

                        hashed_password = hash_password(password)

                        insert_query = """
                        INSERT INTO conference_users (name, email, company, department, password_hash)
                        VALUES (%s, %s, %s, %s, %s)
                        """
                        cursor.execute(insert_query, (name, email, company, department, hashed_password))
                        
                        st.success("Registration successful! You can now sign in.")
                        set_auth_view('login')
                    except mysql.connector.Error as err:
                        st.error(f"Database error during registration: {err}")
                    finally:
                        cursor.close()
        
        st.markdown('</div>', unsafe_allow_html=True) # Close custom card container

    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    if st.button("← Back to Login", key="reg_back_login_btn", use_container_width=True):
        set_auth_view('login')

def render_forgot_password_view():
    """Renders the password reset flow."""
    conn = get_fast_connection()
    
    if 'reset_email' not in st.session_state:
        st.session_state['reset_email'] = None
        st.session_state['email_found'] = False
        
    with st.container(border=False):
        st.markdown('<div class="auth-card-wrapper">', unsafe_allow_html=True)

        with st.form("forgot_pass_email_form", clear_on_submit=False):
            st.markdown("### Find Your Account")
            email_to_check = st.text_input("Enter your registered Email ID", key="forgot_email_input", value=st.session_state.get('reset_email', ''))
            
            if st.form_submit_button("Search Account", type="primary"):
                if not email_to_check:
                    st.warning("Please enter an email address.")
                    return

                cursor = conn.cursor()
                try:
                    check_query = "SELECT id FROM conference_users WHERE email = %s"
                    cursor.execute(check_query, (email_to_check,))
                    user_id = cursor.fetchone()

                    if user_id:
                        st.session_state['reset_email'] = email_to_check
                        st.session_state['email_found'] = True
                        st.success("Account found. Please enter a new password below.")
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
            st.markdown("<hr>")
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
                        cursor = conn.cursor()
                        try:
                            new_hashed_password = hash_password(new_password)
                            
                            update_query = "UPDATE conference_users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE email = %s"
                            cursor.execute(update_query, (new_hashed_password, st.session_state['reset_email']))
                            
                            st.success("Password successfully changed! You can now log in.")
                            
                            st.session_state.email_found = False
                            st.session_state.reset_email = None
                            set_auth_view('login')
                        except mysql.connector.Error as err:
                            st.error(f"Database error during password change: {err}")
                        finally:
                            cursor.close()
        
        st.markdown('</div>', unsafe_allow_html=True) # Close custom card container

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
        header_title = "CONFERENCE BOOKING - SIGN IN"
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

    /* === Global Reset and Gap Removal === */
    html, body {{
        margin: 0 !important;
        padding: 0 !important;
        height: 100%;
        overflow: auto; 
    }}
    .stApp > header {{ visibility: hidden; height: 0; }}
    .stApp .main {{
        padding-top: 0px !important; 
        margin-top: 0px !important;
        min-height: 100vh;
    }}
    div[data-testid="stStatusWidget"] {{
        visibility: hidden;
        height: 0px !important;
        margin-top: 0px !important;
        margin-bottom: 0px !important;
        overflow: hidden;
    }}
    
    /* === FIX: INCREASED PADDING for side corners (block-container) === */
    .stApp .main .block-container {{
        padding-top: 4rem !important; 
        padding-left: 5rem !important;
        padding-right: 5rem !important; 
        max-width: 100% !important;
        /* Center the form content */
        display: flex;
        flex-direction: column;
        align-items: center;
    }}
    
    /* === NEW: Form Card Container Styling (matches dashboard cards) === */
    .auth-card-wrapper {{
        background: #FFFFFF;
        border-radius: 12px;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1); /* Subtle shadow for 3D look */
        padding: 30px 40px; /* Internal padding */
        width: 100%; /* Take full width of its column */
        max-width: 450px; /* Keeps the form from getting too wide on large screens */
        margin-bottom: 20px;
    }}
    
    /* Ensure the Streamlit form inside the card doesn't ruin the padding */
    .auth-card-wrapper form {{
        padding: 0;
    }}
    /* --- End New Card Styling --- */


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
        width: 100vw;
        position: relative; 
        left: 50%;
        right: 50%;
        margin-left: -50vw;
        margin-right: -50vw;
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
    
    /* Input and Button Styling (Kept the same) */
    .stTextInput input,
    .stSelectbox div[data-baseweb="select"] {{
        background-color: #f0f2f6;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px 15px;
        font-size: 16px;
    }}
    .stTextInput input:focus,
    .stSelectbox div[data-baseweb="select"] input:focus {{
        border-color: var(--secondary-color);
        box-shadow: 0 0 0 2px rgba(122, 66, 255, 0.4);
        outline: none;
    }}
    
    /* Primary Button Style */
    .stForm button[kind="primary"] {{
        background: var(--header-gradient) !important;
        color: white !important;
        border: none !important;
        box-shadow: var(--header-box-shadow) !important;
        margin-top: 20px !important;
        width: 100% !important;
    }}
    
    /* Secondary (Navigation) Buttons */
    .stButton > button[key*="conf_new_reg_btn"],
    .stButton > button[key*="conf_forgot_pass_btn"] {{
        /* Use the secondary styling (white/grey) for navigational buttons */
        background: #FFFFFF !important; 
        color: #555555 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        border: 1px solid #E0E0E0 !important;
        font-weight: 500 !important;
        padding: 12px 15px !important; /* Slightly larger padding */
        margin-top: 10px !important; 
        font-size: 14px !important;
        width: 100%;
        border-radius: 8px !important;
    }}
    .stButton > button[key*="back_login_btn"] {{
        /* Back to login button styling */
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
    # The content is now centered using the CSS on .block-container
    if view == 'login':
        render_login_view()
    elif view == 'register':
        render_register_view()
    elif view == 'forgot_password':
        render_forgot_password_view()
        
# -----------------------------------------------------
# --- APP ENTRY POINT ---
# -----------------------------------------------------

if __name__ == '__main__':
    st.set_page_config(layout="wide")

    if st.session_state.get('logged_in'):
        # Placeholder for the main app content if already logged in
        st.title("Conference Dashboard (Logged In)")
        st.write(f"Welcome back, {st.session_state.get('user_name')}!")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()
    else:
        render_conference_login_page()
