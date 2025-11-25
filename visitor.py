import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- SESSION STATE INITIALIZATION ---
if 'visitor_form_step' not in st.session_state:
    st.session_state['visitor_form_step'] = 1
if 'temp_visitor_data' not in st.session_state:
    st.session_state['temp_visitor_data'] = {}
if 'registration_complete' not in st.session_state:
    st.session_state['registration_complete'] = False
if 'visitor_logged_in' not in st.session_state:
    st.session_state['visitor_logged_in'] = False
if 'last_registered_name' not in st.session_state:
    st.session_state['last_registered_name'] = 'Visitor'
if 'visitor_log_data' not in st.session_state:
    st.session_state['visitor_log_data'] = {}

# --- AUTHENTICATION STATE ---
if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'login' # Options: 'login', 'register'
if 'user_db' not in st.session_state:
    # default admin user for testing
    st.session_state['user_db'] = {'admin@company.com': {'password': '123', 'name': 'Admin'}}

# --- CONSTANTS ---
LOGIC_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DISPLAY_TIME_FORMAT = '%I:%M %p'

# --- CSS STYLING ---
def load_custom_css():
    st.markdown("""
        <style>
        /* MAIN CONTAINER SETUP */
        .stApp {
            background-color: #F4F7FE;
        }
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 100% !important;
        }
        
        /* HIDE DEFAULT ELEMENTS */
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* CARD STYLING: Applies to all screen containers (Login/Register/Form/Success) */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
            background-color: white;
            padding: 2.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            margin-bottom: 2rem;
        }

        /* CUSTOM HEADER GRADIENT */
        .visitor-header {
            background: linear-gradient(90deg, #4A56E2 0%, #7B4AE2 100%);
            padding: 25px;
            border-radius: 12px 12px 0 0;
            color: white;
            /* Negative margins to fill the top of the card container */
            margin: -2.5rem -2.5rem 2rem -2.5rem; 
        }

        /* FLEX CONTAINER FOR LOGO/TITLE ALIGNMENT */
        .auth-header-content {
            display: flex;
            align-items: center;
            justify-content: flex-start; /* Aligns content to the start */
            padding: 0 10px;
        }
        .auth-icon {
            font-size: 2.5rem;
            margin-right: 15px;
            line-height: 1; /* Ensures icon alignment */
        }
        .auth-title-box {
            display: flex;
            flex-direction: column;
        }
        .auth-main-title {
            margin: 0; 
            padding: 0; 
            font-weight: 600; 
            line-height: 1.2;
            font-size: 1.8rem;
        }
        .auth-subtitle {
            margin: 0; 
            padding: 0; 
            font-size: 0.9em; 
            opacity: 0.9;
        }
        
        /* INPUT FIELDS */
        .stTextInput > div > div > input {
            border-radius: 8px;
            border: 1px solid #E0E0E0;
            padding: 10px;
            color: #444;
        }
        
        /* BUTTONS (Kept the same) */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #4A56E2 0%, #7B4AE2 100%);
            border: none;
            color: white;
            border-radius: 8px;
            height: 48px;
            font-size: 1rem;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s ease;
        }
        div.stButton > button[kind="secondary"] {
            background-color: transparent;
            color: #666;
            border: 1px solid #ddd;
            border-radius: 8px;
            height: 48px;
            width: 100%;
        }

        /* TABS (Kept the same) */
        .nav-tab {
            font-weight: 600;
            color: #aaa;
            text-align: center;
            padding-bottom: 12px;
            cursor: default;
            font-size: 0.9rem;
        }
        .nav-tab.active {
            color: #4A56E2;
            border-bottom: 3px solid #7B4AE2;
        }
        </style>
    """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def add_visitor_to_log(data):
    current_time = datetime.now()
    new_entry = {
        'Time In Logic': current_time.strftime(LOGIC_TIME_FORMAT),
        'Time In': current_time.strftime(DISPLAY_TIME_FORMAT),
        'Name': data.get('name', 'N/A'),
        'Host': data.get('host', 'N/A'),
        'Company': data.get('company', 'N/A'),
        'Status': 'In Office',
        'Time Out': '',
        'Key': str(current_time.timestamp())
    }
    
    if not st.session_state.get('visitor_log_data'):
        st.session_state['visitor_log_data'] = {key: [] for key in new_entry.keys()}

    for key, value in new_entry.items():
        st.session_state['visitor_log_data'][key].append(value)

def go_back_to_login():
    st.session_state['visitor_logged_in'] = False
    st.session_state['visitor_form_step'] = 1
    st.session_state['temp_visitor_data'] = {}
    st.session_state['registration_complete'] = False
    st.session_state['auth_mode'] = 'login'
    st.rerun()

# --- UI COMPONENTS ---

def render_auth_header(icon, title, subtitle):
    """Renders the header with the icon next to the heading."""
    st.markdown(f"""
        <div class="visitor-header">
            <div class="auth-header-content">
                <span class="auth-icon">{icon}</span>
                <div class="auth-title-box">
                    <h2 class="auth-main-title">{title}</h2>
                    <p class="auth-subtitle">{subtitle}</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_custom_header(title, subtitle="Please fill in your details"):
    """Renders the standard registration header (without icon)."""
    st.markdown(f"""
        <div class="visitor-header">
            <h2 style="margin:0; padding:0; font-weight:600;">{title}</h2>
            <p style="margin:5px 0 0 0; padding:0; font-size: 1em; opacity: 0.9;">{subtitle}</p>
        </div>
    """, unsafe_allow_html=True)

def render_tabs(current_step):
    c1, c2, c3 = st.columns(3)
    def get_tab_html(label, step_num):
        active_class = "active" if current_step == step_num else ""
        return f'<div class="nav-tab {active_class}">{label}</div>'

    with c1: st.markdown(get_tab_html("PRIMARY DETAILS", 1), unsafe_allow_html=True)
    with c2: st.markdown(get_tab_html("SECONDARY DETAILS", 2), unsafe_allow_html=True)
    with c3: st.markdown(get_tab_html("IDENTITY", 3), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# --- SCREENS ---

def auth_screen():
    load_custom_css()
    
    # ADJUSTMENT: Use smaller outer columns to maximize width for fullscreen feel
    col1, col2, col3 = st.columns([0.2, 5, 0.2])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        with st.container():
            # Apply gradient header using the new logo/title renderer
            if st.session_state['auth_mode'] == 'login':
                render_auth_header("📅", "Visitplan Login", "Sign in to manage your bookings and visits")
            else:
                render_auth_header("✍️", "New User Registration", "Create a new account to access the app")

            # --- VIEW: LOGIN ---
            if st.session_state['auth_mode'] == 'login':
                
                with st.form("login_form"):
                    st.markdown("<br>", unsafe_allow_html=True) # Spacer after header
                    email = st.text_input("Email Address", placeholder="you@company.com")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    
                    c_chk, c_link = st.columns([1, 1])
                    with c_chk:
                        st.checkbox("Remember me")
                    with c_link:
                        st.markdown("<div style='text-align: right; color: #4A56E2; cursor: pointer; font-size: 0.9em;'>Forgot password?</div>", unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if st.form_submit_button("Sign In →", type="primary", use_container_width=True):
                        db = st.session_state['user_db']
                        if email in db and db[email]['password'] == password:
                            st.session_state['visitor_logged_in'] = True
                            st.rerun()
                        else:
                            st.error("Invalid email or password")
                
                st.markdown("---")
                if st.button("Don't have an account? Register", type="secondary", use_container_width=True):
                    st.session_state['auth_mode'] = 'register'
                    st.rerun()

            # --- VIEW: REGISTER ---
            elif st.session_state['auth_mode'] == 'register':
                
                with st.form("register_form"):
                    st.markdown("<br>", unsafe_allow_html=True) # Spacer after header
                    reg_name = st.text_input("Full Name", placeholder="John Doe")
                    reg_email = st.text_input("Email Address", placeholder="you@company.com")
                    reg_pass = st.text_input("Password", type="password", placeholder="Create a password")
                    reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if st.form_submit_button("Register & Login →", type="primary", use_container_width=True):
                        if reg_name and reg_email and reg_pass:
                            if reg_pass == reg_confirm:
                                st.session_state['user_db'][reg_email] = {'password': reg_pass, 'name': reg_name}
                                st.success("Account created successfully!")
                                time.sleep(1)
                                st.session_state['visitor_logged_in'] = True
                                st.rerun()
                            else:
                                st.error("Passwords do not match.")
                        else:
                            st.error("Please fill in all fields.")

                st.markdown("---")
                if st.button("Already have an account? Sign In", type="secondary", use_container_width=True):
                    st.session_state['auth_mode'] = 'login'
                    st.rerun()

def registration_form_screen():
    load_custom_css()
    
    # Layout adjustment for full page feel
    c_left, c_main, c_right = st.columns([0.1, 5, 0.1])
    
    with c_main:
        with st.container():
            render_custom_header("Visitor Registration", "Please fill in your details")
            render_tabs(st.session_state['visitor_form_step'])
            
            temp = st.session_state['temp_visitor_data']
            step = st.session_state['visitor_form_step']

            # --- STEP 1: PRIMARY DETAILS ---
            if step == 1:
                with st.form("step1_form", clear_on_submit=False):
                    
                    st.markdown("##### Contact Information")
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # 1. Name
                    name = st.text_input("Full Name", value=temp.get('name', ''), placeholder="John Doe")
                    
                    # 2. Email
                    email = st.text_input("Email Address", value=temp.get('email', ''), placeholder="your.email@example.com")
                    
                    # 3. Phone (Split Column)
                    col_code, col_num = st.columns([1, 4])
                    with col_code:
                        st.selectbox("Country Code", ["IN +91", "US +1", "UK +44"], label_visibility="visible")
                    with col_num:
                        phone = st.text_input("Phone Number", value=temp.get('phone', ''), placeholder="81234 56789")

                    st.markdown("<br><br>", unsafe_allow_html=True)
                    
                    # Buttons
                    b1, b2 = st.columns([1, 1])
                    with b1:
                        if st.form_submit_button("Reset Form", type="secondary", use_container_width=True):
                            st.session_state['temp_visitor_data'] = {}
                            st.rerun()
                    with b2:
                        if st.form_submit_button("Next Step →", type="primary", use_container_width=True):
                            if phone and email and name:
                                st.session_state['temp_visitor_data'].update({'name': name, 'phone': phone, 'email': email})
                                st.session_state['visitor_form_step'] = 2
                                st.rerun()
                            else:
                                st.warning("Please fill in all fields.")

            # --- STEP 2: SECONDARY DETAILS ---
            elif step == 2:
                with st.form("step2_form"):
                    st.markdown("##### Visit Details")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        company = st.text_input("From Company", value=temp.get('company', ''))
                        visit_type = st.selectbox("Visit Type", ["Business", "Personal", "Interview", "Vendor"], index=0)
                    with c2:
                        host = st.selectbox("Who to meet?", ["Select Host", "Alice Admin", "Bob Manager", "Charlie HR"])
                        purpose = st.text_input("Purpose of Visit", value=temp.get('purpose', ''))
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("##### Belongings Declaration")
                    cb1, cb2, cb3, cb4 = st.columns(4)
                    with cb1: bags = st.checkbox("Laptop", value=temp.get('laptop', False))
                    with cb2: docs = st.checkbox("Documents", value=temp.get('documents', False))
                    with cb3: power = st.checkbox("Power Bank", value=temp.get('power', False))
                    with cb4: other = st.checkbox("Other Bags", value=temp.get('other', False))
                    
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    
                    b1, b2 = st.columns([1, 1])
                    with b1:
                        if st.form_submit_button("← Back", type="secondary", use_container_width=True):
                            st.session_state['visitor_form_step'] = 1
                            st.rerun()
                    with b2:
                        if st.form_submit_button("Next Step →", type="primary", use_container_width=True):
                            if host != "Select Host":
                                st.session_state['temp_visitor_data'].update({
                                    'company': company, 'host': host, 'purpose': purpose,
                                    'laptop': bags, 'documents': docs
                                })
                                st.session_state['visitor_form_step'] = 3
                                st.rerun()
                            else:
                                st.error("Please select who you are meeting.")

            # --- STEP 3: IDENTITY ---
            elif step == 3:
                with st.form("step3_form"):
                    st.markdown("##### Identity Verification")
                    
                    c_id, c_sig = st.columns([1, 1])
                    with c_id:
                        st.file_uploader("Upload ID Proof (Optional)", type=['jpg', 'png', 'pdf'])
                    with c_sig:
                        st.info(f"Checking in as: **{temp.get('name')}**")
                        signature = st.text_area("Digital Signature (Type Name)", value=temp.get('signature', ''))
                    
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    
                    b1, b2 = st.columns([1, 1])
                    with b1:
                        if st.form_submit_button("← Back", type="secondary", use_container_width=True):
                            st.session_state['visitor_form_step'] = 2
                            st.rerun()
                    with b2:
                        if st.form_submit_button("Confirm & Sign In", type="primary", use_container_width=True):
                            if signature:
                                st.session_state['temp_visitor_data']['signature'] = signature
                                add_visitor_to_log(st.session_state['temp_visitor_data'])
                                st.session_state['last_registered_name'] = st.session_state['temp_visitor_data'].get('name')
                                st.session_state['registration_complete'] = True
                                st.rerun()
                            else:
                                st.error("Signature required.")

def success_screen():
    load_custom_css()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.container():
            render_custom_header("Check-in Complete! 🎉", "Welcome to the office.")
            st.markdown(f"<h2 style='text-align: center;'>Welcome, {st.session_state['last_registered_name']}!</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #666;'>You have been successfully checked in.</p>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("New Visitor Check-in", type="primary", use_container_width=True):
                st.session_state['registration_complete'] = False
                st.session_state['visitor_form_step'] = 1
                st.session_state['temp_visitor_data'] = {}
                st.rerun()
            if st.button("Log Out", type="secondary", use_container_width=True):
                go_back_to_login()


def visitor_page():
    if st.session_state['registration_complete']:
        success_screen()
    elif st.session_state['visitor_logged_in']:
        registration_form_screen()
    else:
        auth_screen()

# Ensure st.set_page_config is called in main.py, NOT here.
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    visitor_page()