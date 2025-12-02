import streamlit as st
import re
from datetime import datetime
import json
import boto3
from botocore.exceptions import ClientError
import mysql.connector
from mysql.connector import Error

# ==============================================================================
# 1. CONFIGURATION & CREDENTIALS (AWS Integration)
# ==============================================================================

# Constants for AWS and DB
AWS_REGION = "ap-south-1"
# NOTE: The ARN below is a mock value and must be replaced with the actual ARN in a real deployment.
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
DEFAULT_DB_PORT = 3306
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

@st.cache_resource(ttl=3600)
def get_db_credentials():
    """
    Retrieves database credentials ONLY from AWS Secrets Manager.
    The response is cached for 1 hour (3600 seconds).
    """
    # In a real app, you must handle the try/except block. Simplified here for code clarity in the full script.
    # For this demonstration, we'll return mock data to prevent AWS errors in local testing.
    # st.info("Attempting to retrieve DB credentials from AWS Secrets Manager...")
    try:
        # Use an explicit client for Secrets Manager
        client = boto3.client('secretsmanager', region_name=AWS_REGION)
        get_secret_value_response = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        secret = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret)
        
        required_keys = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        if not all(key in secret_dict for key in required_keys):
            raise KeyError("Missing required DB keys in the AWS secret.")

        st.success("DB credentials successfully retrieved.")
        return secret_dict
            
    except Exception:
        # NOTE: Using mock credentials as a fallback for demonstration purposes
        # REPLACE THIS WITH ACTUAL SECRETS MANAGEMENT IN PRODUCTION
        st.warning("Using mock DB credentials (Not connected to AWS Secrets Manager).")
        return {
            "DB_HOST": "localhost",
            "DB_NAME": "mock_db",
            "DB_USER": "mock_user",
            "DB_PASSWORD": "mock_password",
        }

@st.cache_resource(ttl=None)
def get_fast_connection():
    """
    Returns a persistent MySQL connection object.
    Halts the application on initial connection failure.
    Includes a connection ping to ensure the cached connection is active.
    """
    try:
        credentials = get_db_credentials()
            
        # Mocking the connection for non-production environments where credentials fail
        if credentials.get("DB_HOST") == "localhost":
            st.warning("Skipping actual DB connection for mock environment.")
            return None # Return None or a mock connection object

        conn = mysql.connector.connect(
            host=credentials["DB_HOST"],
            user=credentials["DB_USER"],
            password=credentials["DB_PASSWORD"],
            database=credentials["DB_NAME"],
            port=DEFAULT_DB_PORT,
            autocommit=True, # For immediate persistence of changes
            connection_timeout=10,
        )
        conn.ping(reconnect=True)
        st.success("MySQL connection established successfully.")
        return conn
    except EnvironmentError:
        st.stop()
    except Error as err:
        error_msg = f"FATAL: MySQL Connection Error: Cannot connect. Details: {err.msg}"
        st.error(error_msg)
        st.stop()
    except Exception as e:
        error_msg = f"FATAL: Unexpected Connection Error: {type(e).__name__} - {e}"
        st.error(error_msg)
        st.stop()


# ==============================================================================
# 2. CONFIGURATION & STATE SETUP
# ==============================================================================

def initialize_session_state():
    """Initializes all necessary session state variables if they do not exist."""
    
    # App Flow State: 'login', 'forgot_password', 'dashboard' (Registration flow removed)
    if 'app_flow' not in st.session_state:
        st.session_state['app_flow'] = 'login' # Start on login
        
    # Registration flow state (now obsolete but kept for safety if later code references it)
    if 'registration_step' not in st.session_state:
        st.session_state['registration_step'] = None
    if 'visitor_data' not in st.session_state:
        st.session_state['visitor_data'] = {}
    
    # Global state (for login)
    if 'company_id' not in st.session_state:
        st.session_state['company_id'] = None
    if 'admin_logged_in' not in st.session_state:
        st.session_state['admin_logged_in'] = False


def navigate_to_login_screen():
    """Clears state and sets the flow back to the login page."""
    
    st.session_state['app_flow'] = 'login'
    st.session_state['registration_step'] = None
    st.session_state['visitor_data'] = {}
    st.rerun()

# ==============================================================================
# 3. DATABASE INTERACTION & SERVICE
# ==============================================================================

# NOTE: save_visitor_data_to_db is no longer needed but kept empty for reference 
# in case it's called accidentally, or if dashboard features visitor check-in later.

def save_visitor_data_to_db(data):
    """
    Placeholder for the DB save function.
    Since the registration form is removed, this function is effectively disabled.
    """
    st.error("Visitor registration form is removed. Data cannot be saved.")
    return False

# ==============================================================================
# 4. HELPER FUNCTIONS (CSS and Header)
# ==============================================================================

def render_custom_styles():
    """Applies custom CSS for the header banner and buttons."""
    logo_svg_data = """
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L2 22H22L12 2Z" fill="#FFFFFF"/>
        <path d="M12 7L16 15H8L12 7Z" fill="#5d28a5"/>
    </svg>
    """

    st.markdown(
        f"""
        <style>
        /* General layout and font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap');
        .stApp {{
            font-family: 'Inter', sans-serif;
        }}
        
        /* Header Banner Styling */
        .header-banner {{
            background-color: #5d28a5; /* Deep Purple */
            color: white;
            padding: 15px 20px;
            font-size: 1.8em;
            font-weight: 700;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .zodopt-tag {{
            display: flex;
            align-items: center;
            font-size: 0.6em;
            font-weight: 400;
            gap: 5px;
        }}
        
        /* Step Navigation Tabs - REMOVED */
        .step-tabs {{
            display: none;
        }}
        
        /* Streamlit Button Overrides */
        /* Style for the "Next" / "Submit" button (Red/Pink/Accent) */
        div.stFormSubmitButton > button, div.stFormSubmitButton > button:focus:not(:active) {{
            background-color: #ff545d; /* Pink/Red Accent */
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
            transition: background-color 0.2s;
        }}
        div.stFormSubmitButton > button:hover {{
            background-color: #e54c52;
        }}
        
        /* Style for all standard st.button (Previous/Reset/Main Menu) */
        div.stButton > button, div.stButton > button:focus:not(:active) {{ 
            background-color: #f0f0f0;
            color: #555;
            border: 1px solid #ccc;
            padding: 10px 20px;
            border-radius: 8px;
            transition: background-color 0.2s;
        }}
        div.stButton > button:hover {{
            background-color: #e5e5e5;
        }}
        
        /* Login/Registration Button */
        .stButton button[kind="primary"] {{
            background-color: #5d28a5;
            border-color: #5d28a5;
            color: white;
        }}
        .stButton button[kind="primary"]:hover {{
            background-color: #4b2085;
            border-color: #4b2085;
        }}
        </style>
        """, 
        unsafe_allow_html=True
    )
    return logo_svg_data

def render_app_header():
    """Renders the simplified main application header banner."""
    logo_svg = render_custom_styles()
    company_id = st.session_state.get('company_id', 'N/A')
    
    st.markdown(
        f"""
        <div class="header-banner">
            VISITOR MANAGEMENT SYSTEM (Company ID: {company_id})
            <div class="zodopt-tag">
                zodopt
                {logo_svg}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
def render_step_navigation(current_step):
    """Renders the step navigation tabs only during the registration flow. (Now disabled)"""
    st.markdown(
        """
        """,
        unsafe_allow_html=True
    )

# ==============================================================================
# 5. ADMIN LOGIN AND FORGOT PASSWORD (REFINED)
# ==============================================================================

def render_admin_login_page():
    """Renders the login form for the admin, allowing navigation to forgot password."""
    
    st.title("Admin Login Required")
    st.markdown("Please enter your credentials to access the Visitor Management System.")

    # Centered container for the login form
    with st.container(border=True):
        st.markdown("---")
        # Dummy credentials for this example
        st.markdown("For testing: Username: **admin** | Password: **password** | Company ID: **1**")
        st.markdown("---")
        
        with st.form("admin_login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            company_id_input = st.text_input("Company ID (e.g., 1)")
            
            submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)

            if submitted:
                # Simple, hardcoded check for demonstration (replace with DB check in production)
                if username == "admin" and password == "password" and company_id_input.isdigit():
                    st.session_state['admin_logged_in'] = True
                    st.session_state['company_id'] = int(company_id_input) 
                    st.success(f"Login successful for Company ID: {st.session_state['company_id']}")
                    st.balloons()
                    # Change flow state to dashboard after success
                    st.session_state['app_flow'] = 'dashboard'
                    st.rerun()
                else:
                    st.error("Invalid Username, Password, or Company ID.")
    
    # Navigation links below the form
    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Forgot Password?", key="forgot_password_link"):
            st.session_state['app_flow'] = 'forgot_password'
            st.rerun()
    with col2:
        # Link to the visitor registration (Now disabled/removed)
        st.button("Visitor Registration (Removed)", key="visitor_reg_link", disabled=True)


def render_forgot_password_page():
    """Mock page for handling password recovery/reset."""
    
    st.title("Password Recovery")
    st.warning("⚠️ This feature is mocked. In a production environment, this would trigger an email or SMS code.")

    with st.form("forgot_password_form"):
        st.markdown("### Reset Your Password")
        recovery_email = st.text_input("Enter your registered Email Address")
        
        submitted = st.form_submit_button("Send Recovery Link", type="primary", use_container_width=True)
        
        if submitted:
            if re.match(EMAIL_REGEX, recovery_email):
                st.success(f"A mock recovery link has been sent to **{recovery_email}**.")
                st.info("Check your email to reset your password. Returning to login page now...")
                import time
                time.sleep(2)
                navigate_to_login_screen()
            else:
                st.error("Please enter a valid email address.")

    if st.button("← Back to Login", key="back_to_login_from_forgot"):
        navigate_to_login_screen()

# ==============================================================================
# 6. DASHBOARD (Simulated)
# ==============================================================================

def render_dashboard_simulation():
    """Simulates the navigation to a separate visitor_dashboard.py."""
    
    st.title("Admin Dashboard Simulation 🚀")
    st.subheader(f"Access Granted for Company ID: {st.session_state['company_id']}")
    
    st.markdown("---")
    
    st.success("""
        **Success!** The login process is complete. 
        
        This space now represents the separate `visitor_dashboard.py` file.
    """)
    
    st.markdown("### Dashboard Actions (Simulated):")
    st.warning(
        """
        The Visitor Registration form has been removed from this file. 
        All visitor check-in functionality would need to be implemented 
        within the **`visitor_dashboard.py`** file itself.
        """
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.button("View Visitor Logs (WIP)", key="view_logs_from_dash", use_container_width=True, disabled=True)
    with col2:
        if st.button("Log Out", key="logout_from_dash", use_container_width=True):
            st.session_state['admin_logged_in'] = False
            st.session_state['company_id'] = None
            navigate_to_login_screen()

# ==============================================================================
# 7. VISITOR REGISTRATION FLOW (REMOVED)
# ==============================================================================
# This section has been completely removed as requested.

# ==============================================================================
# 8. Main Application Logic
# ==============================================================================

def main_app_flow():
    """Main function to run the application, handling flow between login, dashboard, and registration."""
    
    initialize_session_state()
    render_app_header()
    
    current_flow = st.session_state.get('app_flow')

    if current_flow == 'login':
        render_admin_login_page()
    
    elif current_flow == 'forgot_password':
        render_forgot_password_page()
    
    elif current_flow == 'dashboard':
        # Check connection health before proceeding
        conn = get_fast_connection()
        if conn is not None and not conn.is_connected():
            st.error("Database connection lost. Please re-login.")
            st.session_state['admin_logged_in'] = False
            st.session_state['company_id'] = None
            st.session_state['app_flow'] = 'login'
            st.rerun()
        
        render_dashboard_simulation() # Simulate the content of visitor_dashboard.py
    
    # The 'registration' flow state is no longer handled
    # elif current_flow == 'registration':
    #     render_registration_flow()

if __name__ == "__main__":
    main_app_flow()
