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
from typing import Dict, Any, Optional

# ==============================================================================
# 1. CONFIGURATION & CREDENTIALS
# ==============================================================================

AWS_REGION = "ap-south-1" 
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

LOGO_PATH = "zodopt.png" 
LOGO_PLACEHOLDER_TEXT = "zodopt"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"
MIN_PASSWORD_LENGTH = 8
DEFAULT_DB_PORT = 3306

# --- AWS SECRET MANAGER ----------------
@st.cache_resource
def get_db_credentials() -> Dict[str, str]:
    if not AWS_SECRET_NAME:
        st.error("FATAL: AWS_SECRET_NAME is not configured. Cannot proceed.")
        st.stop()
        
    try:
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        creds = json.loads(resp["SecretString"])

        required_keys = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        for k in required_keys:
            if k not in creds:
                raise RuntimeError(f"Missing DB key: {k}")
        return creds
        
    except Exception as e:
        st.error("Could not retrieve DB credentials from AWS Secrets Manager.")
        st.write(e)
        st.stop()

# ---------------- FAST DB CONNECTION ----------------
@st.cache_resource
def get_fast_connection() -> mysql.connector.connection.MySQLConnection:
    credentials = get_db_credentials()
    try:
        conn = mysql.connector.connect(
            host=credentials["DB_HOST"],
            user=credentials["DB_USER"],
            password=credentials["DB_PASSWORD"],
            database=credentials["DB_NAME"],
            port=DEFAULT_DB_PORT,
            autocommit=True,
            connection_timeout=10,
        )
        return conn
    except Exception as e:
        st.error("Database connection error.")
        st.write(e)
        st.stop()

# ==============================================================================
# 2. SECURITY AND UTILITY HELPERS
# ==============================================================================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode()

def check_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed_password.encode())
    except:
        return False

def _get_image_base64(path: str) -> str:
    return ""

def set_auth_view(view: str):
    st.session_state['visitor_auth_view'] = view
    if 'reset_user_id' in st.session_state:
        del st.session_state['reset_user_id']
    sleep(0.1)
    st.rerun()

# ==============================================================================
# 3. DB FUNCTIONS
# ==============================================================================

def get_admin_by_email(conn, email: str) -> Optional[Dict[str, Any]]:
    query = """
    SELECT au.id, au.password_hash, au.name, c.id AS company_id, c.company_name
    FROM admin_users au
    JOIN companies c ON au.company_id = c.id
    WHERE au.email = %s AND au.is_active = 1;
    """
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, (email,))
            return cursor.fetchone()
    except:
        return None

def create_company_and_admin(conn, company_name, admin_name, email, password_hash):
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO companies (company_name) VALUES (%s)", (company_name,))
            company_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO admin_users (company_id, name, email, password_hash, is_active)
                VALUES (%s, %s, %s, %s, 1)
            """, (company_id, admin_name, email, password_hash))
            conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error("Registration failed.")
        st.write(e)
        return False

def update_admin_password_directly(conn, user_id: int, new_hash: str) -> bool:
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE admin_users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
            conn.commit()
        return True
    except:
        conn.rollback()
        return False

# ==============================================================================
# 4. VIEW COMPONENTS
# ==============================================================================

def render_admin_register_view():
    conn = get_fast_connection()
    with st.form("admin_register_form"):
        st.markdown("### New Admin Registration")
        company_name = st.text_input("Company Name")
        admin_name = st.text_input("Admin Full Name")
        admin_email = st.text_input("Email ID").lower()
        st.markdown("---")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Create Company & Admin Account", type="primary")

        if submitted:
            if password == confirm_password and len(password) >= MIN_PASSWORD_LENGTH:
                hashed = hash_password(password)
                if create_company_and_admin(conn, company_name, admin_name, admin_email, hashed):
                    st.success("Registration successful!")
                    set_auth_view('admin_login')

    st.button("Existing Admin Login", key="existing_admin", use_container_width=True, on_click=lambda: set_auth_view('admin_login'))
    st.button("Forgot Password?", key="reg_forgot", use_container_width=True, on_click=lambda: set_auth_view('forgot_password'))

def render_existing_admin_login_view():
    conn = get_fast_connection()

    with st.form("admin_login_form"):
        st.markdown("### Admin Sign In")
        email = st.text_input("Admin Email ID").lower()
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Admin Sign In →", type="primary")

        if submitted:
            user = get_admin_by_email(conn, email)
            if user and check_password(password, user['password_hash']):
                st.session_state['admin_logged_in'] = True
                st.session_state['admin_id'] = user['id']
                st.session_state['admin_name'] = user['name']
                st.session_state['company_id'] = user['company_id']
                st.session_state['company_name'] = user['company_name']
                set_auth_view('admin_dashboard_home')
            else:
                st.error("Invalid credentials")

    st.button("← New Registration", key="admin_new_reg", use_container_width=True, on_click=lambda: set_auth_view('admin_register'))
    st.button("Forgot Password?", key="admin_forgot", use_container_width=True, on_click=lambda: set_auth_view('forgot_password'))

def render_admin_dashboard_home_view():
    if not st.session_state.get('admin_logged_in'):
        st.warning("Please log in.")
        set_auth_view('admin_login')
        return

    st.session_state['current_page'] = 'visitor_dashboard'
    st.rerun()

def render_forgot_password_view():
    conn = get_fast_connection()

    if 'reset_user_id' not in st.session_state:
        st.subheader("1. Verify Admin Email ID")
        with st.form("forgot_check"):
            email = st.text_input("Enter Email ID").lower()
            submitted = st.form_submit_button("Check Email", type="primary")
            if submitted:
                user = get_admin_by_email(conn, email)
                if user:
                    st.session_state['reset_user_id'] = user['id']
                    st.success("Email verified.")
                    st.rerun()
                else:
                    st.error("Email not found")
    else:
        st.subheader("2. Set New Password")
        with st.form("forgot_reset"):
            new_pass = st.text_input("New Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Reset Password", type="primary")

            if submitted and new_pass == confirm and len(new_pass) >= MIN_PASSWORD_LENGTH:
                hashed = hash_password(new_pass)
                if update_admin_password_directly(conn, st.session_state['reset_user_id'], hashed):
                    st.success("Password updated")
                    del st.session_state['reset_user_id']
                    set_auth_view('admin_login')

    st.button("← Back to Admin Login", key="forgot_back", use_container_width=True, on_click=lambda: set_auth_view('admin_login'))

# ==============================================================================
# 5. MAIN PAGE WITH UPDATED HEADER
# ==============================================================================

def render_visitor_login_page():

    if 'visitor_auth_view' not in st.session_state:
        st.session_state['visitor_auth_view'] = 'admin_login'

    view = st.session_state['visitor_auth_view']

    header_titles = {
        'admin_register': "ADMIN REGISTRATION",
        'admin_login': "ADMIN LOGIN",
        'admin_dashboard_home': "DASHBOARD",
        'forgot_password': "RESET PASSWORD"
    }
    header_title = header_titles.get(view, "ADMIN PORTAL")

    # ---- UPDATED COMPACT PROFESSIONAL HEADER CSS ----
    st.markdown(f"""
    <style>
    :root {{
        --header-gradient: {HEADER_GRADIENT};
    }}

    .stApp > header {{visibility: hidden;}}

    .header-box {{
        background: var(--header-gradient);
        padding: 14px 32px !important;
        margin-bottom: 28px !important;
        border-radius: 0 0 12px 12px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.15) !important;
        width: 100vw !important;
        margin-left: calc(50% - 50vw) !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
    }}

    .header-title {{
        font-size: 24px !important;
        font-weight: 700 !important;
        color: white !important;
        margin: 0px !important;
        letter-spacing: 1px;
    }}

    .header-logo-img {{
        height: 42px !important;
        object-fit: contain;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ---- HEADER RENDER ----
    if os.path.exists(LOGO_PATH):
        st.markdown(
            f"""
            <div class="header-box">
                <div class="header-title">{header_title}</div>
                <img src="{LOGO_PATH}" class="header-logo-img">
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="header-box">
                <div class="header-title">{header_title}</div>
                <div style="color:white;font-weight:bold;">{LOGO_PLACEHOLDER_TEXT}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ---- ROUTING ----
    if view == 'admin_register':
        render_admin_register_view()
    elif view == 'admin_login':
        render_existing_admin_login_view()
    elif view == 'admin_dashboard_home':
        render_admin_dashboard_home_view()
    elif view == 'forgot_password':
        render_forgot_password_view()

# ==============================================================================
# START
# ==============================================================================
if __name__ == '__main__':
    render_visitor_login_page()
