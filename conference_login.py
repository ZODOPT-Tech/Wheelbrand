import streamlit as st
import boto3
import json
import mysql.connector
import bcrypt
# Note: pandas and datetime are not strictly needed for login but kept for completeness if you reuse this file structure.

# ==============================
# CONFIG
# ==============================
AWS_REGION = "ap-south-1"
# AWS_SECRET_NAME is used in the login app
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
# Renamed from HEADER_GRADIENT to GRADIENT for consistency with the provided code
GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


# ==============================
# DB CONNECTION
# ==============================
@st.cache_resource
def get_db_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(resp["SecretString"])


@st.cache_resource
def get_connection():
    c = get_db_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True
    )


# ==============================
# PASSWORD SECURITY
# ==============================
def verify_password(input_password, db_hash):
    return bcrypt.checkpw(input_password.encode(), db_hash.encode())


# ==============================
# CSS (Updated to match the Dashboard's style)
# ==============================
def inject_css():
    st.markdown(f"""
    <style>

    /* Layout reset (from Dashboard) */
    header[data-testid="stHeader"] {{display:none;}}
    .block-container {{padding-top:0;}}
    .block-container {{
        padding: 0 !important;
        max-width: 100% !important;
    }}

    /* Global Body Style */
    body {{
        background: #F6F8FF;
        font-family: 'Inter', sans-serif;
    }}

    /* Header section (from Dashboard) */
    .header-box {{
        background:{GRADIENT};
        /* Adjusted margins for the login page to occupy the full top width */
        margin:-1rem -1rem 1.5rem -1rem; 
        border-radius:0 0 20px 20px; /* Adjusted to look like a full header, keeping the bottom curve */
        padding:28px 40px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 6px 20px rgba(0,0,0,0.18);
    }}

    .welcome {{ /* Reusing Dashboard style for title */
        font-size:32px;
        font-weight:900;
        color:white;
        margin-bottom:5px;
    }}
    .header-logo {{ /* Reusing Dashboard style for logo */
        height:60px;
    }}

    /* Login card box (Preserved from original login code) */
    .login-card {{
        width:440px;
        margin:70px auto;
        background:white;
        border-radius:18px;
        padding:34px 30px;
        box-shadow:0 4px 18px rgba(0,0,0,0.08);
    }}

    /* Input Fields (Preserved from original login code) */
    .stTextInput > div > div > input {{
        background:#F2F4FA;
        padding:14px;
        border-radius:10px;
        font-size:16px;
    }}

    /* Main button (Preserved from original login code) */
    .primary-btn {{
        background:{GRADIENT} !important;
        color:white !important;
        font-weight:700 !important;
        border:none !important;
        padding:14px !important;
        width:100%;
        border-radius:12px !important;
        font-size:16px !important;
        box-shadow:0 6px 22px rgba(80,48,157,0.4) !important;
    }}

    .primary-btn:hover {{
        opacity:0.93;
        transform:translateY(-1px);
    }}
    
    /* Secondary buttons inside the card (For Register/Forgot) */
    .stButton > button {{
        margin-top: 10px;
        font-size: 14px;
        /* Ensure these buttons don't inherit the main button style */
        background: none !important; 
        color: #50309D !important;
        border: none !important;
        box-shadow: none !important;
    }}

    @media(max-width:600px) {{
        .login-card {{
            width:92%;
        }}
        .welcome {{
            font-size:24px;
        }}
        .header-box {{
            padding:20px;
        }}
        .header-logo {{
            height:50px;
        }}
    }}

    </style>
    """, unsafe_allow_html=True)


# ==============================
# LOGIN FLOW
# ==============================
def render_login_view():
    conn = get_connection()

    with st.container():
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        with st.form("login"):
            email = st.text_input("Email")
            pwd = st.text_input("Password", type="password")

            if st.form_submit_button("Sign In →", type="primary", use_container_width=True):
                if not email or not pwd:
                    st.error("Enter email and password")
                else:
                    cur = conn.cursor(dictionary=True)
                    cur.execute("SELECT id,name,password_hash FROM conference_users WHERE email=%s AND is_active=1", (email,))
                    user = cur.fetchone()

                    if user and verify_password(pwd, user['password_hash']):
                        st.session_state['user_id'] = user['id']
                        st.session_state['current_page'] = "conference_dashboard"
                        st.rerun()
                    else:
                        st.error("Invalid login details")
            
            # Footer buttons moved inside the form/card as requested
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                # Changed type to 'secondary' to distinguish from 'Sign In'
                if st.button("New Registration", type="secondary", use_container_width=True):
                    st.session_state['conf_auth_view'] = 'register'
                    st.rerun()
            with col2:
                # Changed type to 'secondary' to distinguish from 'Sign In'
                if st.button("Forgot Password?", type="secondary", use_container_width=True):
                    st.session_state['conf_auth_view'] = 'forgot_password'
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


# ==============================
# PLACEHOLDER PAGES
# ==============================
def render_register_view():
    st.write("Registration Page")


def render_forgot_view():
    st.write("Forgot Password Page")


# ==============================
# ROUTER
# ==============================
def render_conference_login_page():
    inject_css()

    if 'conf_auth_view' not in st.session_state:
        st.session_state['conf_auth_view'] = 'login'

    # Header
    st.markdown(f"""
    <div class='header-box'>
        <div>
            <div class='welcome'>Conference Login</div>
        </div>
        <img src="{LOGO_URL}" class="header-logo">
    </div>
    """, unsafe_allow_html=True)

    view = st.session_state['conf_auth_view']
    if view == "login":
        render_login_view()
    elif view == "register":
        render_register_view()
    else:
        render_forgot_view()
