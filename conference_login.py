import streamlit as st
import os
import base64

# --- Configuration (Shared Constants) ---
LOGO_PATH = r"zodopt.png"
LOGO_PLACEHOLDER_TEXT = "zodopt"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)" # Primary Color for header and main buttons

# --- Utility Function ---
def _get_image_base64(path):
    """Converts a local image file to a base64 string for embedding in HTML/CSS."""
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""

# --- Dummy Database (For demonstration) ---
# Replace this with your actual database access logic
users_db = {
    "conf.user@example.com": {"password": "confpass123", "name": "Jane Doe", "company": "TechCorp"},
    "test@zodopt.com": {"password": "testpass", "name": "John Smith", "company": "Zodopt"},
}

# --- State Management Helper ---
def set_auth_view(view):
    """Changes the current authentication view (login, register, forgot_password)."""
    st.session_state['conf_auth_view'] = view
    st.rerun()

# -----------------------------------------------------
# --- VIEW RENDERING FUNCTIONS (REMOVED H2 HEADINGS) ---
# -----------------------------------------------------

def render_login_view():
    """Renders the standard login form."""
    # 1. Removed "Delegate Login" heading to simplify the view.
    
    with st.form("conf_login_form"):
        email = st.text_input("Email ID", key="conf_login_email")
        password = st.text_input("Password", type="password", key="conf_login_password")
        
        submitted = st.form_submit_button("Sign In →", type="primary")
        
        if submitted:
            user_data = users_db.get(email)
            if user_data and user_data['password'] == password:
                st.success(f"Welcome, {user_data['name']}! Logged in successfully.")
                st.session_state['current_page'] = 'conference_dashboard' 
                st.session_state['user_email'] = email
                st.rerun()
            else:
                st.error("Invalid Email ID or Password.")
    
    # Navigation Buttons (These are now primary-styled via CSS, as requested)
    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Registration", key="conf_new_reg_btn", use_container_width=True):
            set_auth_view('register')
    with col2:
        if st.button("Forgot Password?", key="conf_forgot_pass_btn", use_container_width=True):
            set_auth_view('forgot_password')

def render_register_view():
    """Renders the new delegate registration form."""
    # The main header title is now dynamically set to "NEW REGISTRATION"
    
    with st.form("conf_register_form"):
        name = st.text_input("Name", key="reg_name")
        email = st.text_input("Email ID", key="reg_email")
        company = st.text_input("Company", key="reg_company")
        password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
        
        submitted = st.form_submit_button("Register Account", type="primary")

        if submitted:
            if not all([name, email, company, password, confirm_password]):
                st.error("Please fill in all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif email in users_db:
                st.error("This Email ID is already registered.")
            else:
                users_db[email] = {"password": password, "name": name, "company": company}
                st.success("Registration successful! Please sign in.")
                set_auth_view('login')
    
    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    if st.button("← Back to Login", key="reg_back_login_btn", use_container_width=True):
        set_auth_view('login')

def render_forgot_password_view():
    """Renders the two-step password reset flow."""
    # The main header title is now dynamically set to "RESET PASSWORD"
    
    if 'reset_email' not in st.session_state:
        st.session_state['reset_email'] = None
        st.session_state['email_found'] = False
        
    # --- Step 1: Email Input (Search Account) ---
    with st.form("forgot_pass_email_form", clear_on_submit=False):
        email_to_check = st.text_input("Enter your registered Email ID", key="forgot_email_input", value=st.session_state.get('reset_email', ''))
        
        # This button is styled as primary gradient
        if st.form_submit_button("Search Account", type="primary"):
            if email_to_check in users_db:
                st.session_state['reset_email'] = email_to_check
                st.session_state['email_found'] = True
                st.success("Account found. Please enter a new password below.")
                st.rerun() 
            else:
                st.session_state['email_found'] = False
                st.error("Email ID not found in our records.")

    # --- Step 2: Password Reset (If Email Found) ---
    if st.session_state.email_found:
        with st.form("forgot_pass_reset_form"):
            new_password = st.text_input("New Password", type="password", key="reset_new_password")
            confirm_password = st.text_input("Confirm New Password", type="password", key="reset_confirm_password")
            
            # This button is styled as primary gradient
            if st.form_submit_button("Change Password", type="primary"):
                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    users_db[st.session_state['reset_email']]['password'] = new_password
                    st.success("Password successfully changed! You can now log in.")
                    
                    st.session_state.email_found = False
                    st.session_state.reset_email = None
                    set_auth_view('login')

    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    if st.button("← Back to Login", key="forgot_back_login_btn", use_container_width=True):
        st.session_state.email_found = False
        st.session_state.reset_email = None
        set_auth_view('login')


# -----------------------------------------------------
# --- MAIN FUNCTION (Dynamically sets header title) ---
# -----------------------------------------------------

def render_conference_login_page():
    # Initialize the view state
    if 'conf_auth_view' not in st.session_state:
        st.session_state['conf_auth_view'] = 'login'

    # Determine the header title based on the current view state
    view = st.session_state['conf_auth_view']
    if view == 'login':
        header_title = "CONFERENCE BOOKING" # Keep the original title for the login page
    elif view == 'register':
        header_title = "NEW REGISTRATION"  # Change header title for registration
    elif view == 'forgot_password':
        header_title = "RESET PASSWORD"     # Change header title for reset password
        
    # 1. Inject Custom CSS (Ensuring all relevant buttons use the gradient)
    st.markdown(f"""
    <style>
    /* Use a CSS variable for the gradient to maintain consistency */
    :root {{
        --header-gradient: {HEADER_GRADIENT};
        --header-box-shadow: 0 4px 10px rgba(80, 48, 157, 0.4);
    }}

    /* Global Streamlit overrides for login page */
    html, body {{
        margin-top: 0 !important;
        padding-top: 0 !important;
        overflow-x: hidden;
    }}
    .stApp .main {{
        padding-top: 0px !important; 
        margin-top: 0px !important;
    }}
    .stApp > header {{ visibility: hidden; }}
    
    /* Header Box - Full Width */
    .header-box {{
        background: var(--header-gradient);
        padding: 20px 40px;
        margin-top: 0px; 
        margin-bottom: 40px;
        border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: calc(100% + 4rem); 
        margin-left: -2rem; 
        margin-right: -2rem; 
    }}
    .header-title {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
        font-size: 34px;
        font-weight: 800;
        color: #FFFFFF; 
        letter-spacing: 1.5px;
        margin: 0;
    }}

    /* Login Form Specific Styles */
    h2 {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #333333;
        margin-top: 20px;
        margin-bottom: 30px;
        font-weight: 600;
    }}
    .stTextInput label {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #555555;
        font-weight: 500;
        margin-bottom: 5px;
    }}
    .stTextInput input, .stTextInput > div > div > input {{
        background-color: #f0f2f6;
        border: none;
        border-radius: 8px;
        padding: 15px 15px;
        font-size: 16px;
        color: #333333;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.06);
        transition: all 0.2s ease;
    }}
    .stTextInput input:focus {{
        box-shadow: 0 0 0 2px #7A42FF80;
        outline: none;
    }}
    
    /* Primary Button Style (for Sign In, Register, Change Password - inside forms) */
    .stForm button[kind="primary"] {{
        background: var(--header-gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 15px 20px !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        box-shadow: var(--header-box-shadow) !important;
        margin-top: 30px !important;
        width: 100% !important;
        transition: all 0.2s ease;
    }}
    .stForm button[kind="primary"]:hover {{
        opacity: 0.9;
        transform: translateY(-1px);
    }}
    
    /* Secondary Buttons (New Registration, Forgot Password) - outside forms. 
       These are now styled with the primary gradient as requested. */
    .stButton > button:not([key*="back_login_btn"]) {{
        background: var(--header-gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 15px 20px !important; /* Slightly larger padding for prominence */
        font-size: 15px !important;
        font-weight: 600 !important;
        box-shadow: var(--header-box-shadow) !important;
        margin-top: 15px !important; 
        transition: all 0.2s ease;
    }}
    .stButton > button:not([key*="back_login_btn"]):hover {{
        opacity: 0.9;
        transform: translateY(-1px);
    }}
    
    /* Special override to keep the back-to-login button less prominent */
    .stButton > button[key*="back_login_btn"],
    .stButton > button[key*="conf_back_main_btn"] {{
        background: #F0F2F6 !important; 
        color: #555555 !important;
        box-shadow: none !important;
        border: 1px solid #E0E0E0 !important;
        font-weight: 500 !important;
        padding: 10px 15px !important;
    }}
    .stButton > button[key*="back_login_btn"]:hover,
    .stButton > button[key*="conf_back_main_btn"]:hover {{
        background: #E0E0E0 !important;
        transform: none;
    }}
    </style>
    """, unsafe_allow_html=True)


    # 2. HEADER (Dynamic Title)
    if os.path.exists(LOGO_PATH):
        logo_html = f'<img src="data:image/png;base64,{_get_image_base64(LOGO_PATH)}" class="header-logo-img" style="height: 50px; border-radius: 8px;">'
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
    if view == 'login':
        render_login_view()
    elif view == 'register':
        render_register_view()
    elif view == 'forgot_password':
        render_forgot_password_view()
    
