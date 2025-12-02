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
HEADER_GRADIENT = "linear-gradient(90deg, #4B2ECF, #7A42FF)"  # Updated gradient for premium look
MIN_PASSWORD_LENGTH = 8
DEFAULT_DB_PORT = 3306

# ---------------- AWS SECRET MANAGER ----------------
@st.cache_resource
def get_db_credentials() -> Dict[str, str]:
    try:
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        creds = json.loads(resp["SecretString"])
        return creds
    except Exception as e:
        st.error("Could not load DB credentials.")
        st.stop()

@st.cache_resource
def get_fast_connection():
    creds = get_db_credentials()
    try:
        conn = mysql.connector.connect(
            host=creds["DB_HOST"],
            user=creds["DB_USER"],
            password=creds["DB_PASSWORD"],
            database=creds["DB_NAME"],
            port=DEFAULT_DB_PORT,
            autocommit=True,
        )
        return conn
    except:
        st.error("DB connection failed.")
        st.stop()

# ==============================================================================
# SECURITY HELPERS
# ------------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def set_auth_view(view: str):
    st.session_state['visitor_auth_view'] = view
    sleep(0.1)
    st.rerun()

# ==============================================================================
# DB Queries
# ------------------------------------------------------------------------------
def get_admin_by_email(conn, email: str):
    q = """
    SELECT au.id, au.password_hash, au.name, c.id AS company_id, c.company_name
    FROM admin_users au
    JOIN companies c ON au.company_id = c.id
    WHERE au.email=%s AND au.is_active=1
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute(q, (email,))
    return cursor.fetchone()

def create_company_and_admin(conn, cname, aname, email, hashed):
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO companies (company_name) VALUES (%s)", (cname,))
        cid = cursor.lastrowid

        cursor.execute("""
            INSERT INTO admin_users (company_id, name, email, password_hash, is_active)
            VALUES (%s,%s,%s,%s,1)
        """, (cid, aname, email, hashed))
        conn.commit()
        return True
    except:
        conn.rollback()
        return False

def update_admin_password_directly(conn, uid: int, newhash: str):
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE admin_users SET password_hash=%s WHERE id=%s", (newhash, uid))
        conn.commit()
        return True
    except:
        conn.rollback()
        return False

# ==============================================================================
# 4. FORMS (Login/Register/Reset)
# ==============================================================================

def render_admin_register_view():
    conn = get_fast_connection()
    with st.form("reg_form"):
        st.markdown("### New Admin Registration")
        cname = st.text_input("Company Name")
        aname = st.text_input("Admin Name")
        email = st.text_input("Email").lower()
        pass1 = st.text_input("Password", type="password")
        pass2 = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register", type="primary")

        if submit:
            if pass1 == pass2 and len(pass1) >= MIN_PASSWORD_LENGTH:
                if create_company_and_admin(conn, cname, aname, email, hash_password(pass1)):
                    st.success("Registration successful")
                    set_auth_view("admin_login")
            else:
                st.error("Invalid password")

    # TWO BUTTONS NEXT TO EACH OTHER — SAME COLOR AS HEADER
    col1, col2 = st.columns(2)
    col1.button("Back to Login", key="reg_back", on_click=lambda: set_auth_view("admin_login"))
    col2.button("Forgot Password?", key="reg_fp", on_click=lambda: set_auth_view("forgot_password"))

def render_existing_admin_login_view():
    conn = get_fast_connection()
    with st.form("login_form"):
        st.markdown("### Admin Login")
        email = st.text_input("Email").lower()
        passw = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In →", type="primary")

        if submit:
            user = get_admin_by_email(conn, email)
            if user and check_password(passw, user['password_hash']):
                st.session_state['admin_logged_in'] = True
                st.session_state['admin_id'] = user['id']
                st.session_state['admin_name'] = user['name']
                st.session_state['company_id'] = user['company_id']
                st.session_state['company_name'] = user['company_name']
                set_auth_view("admin_dashboard_home")
            else:
                st.error("Invalid login")

    # TWO BUTTONS SIDE-BY-SIDE — SAME COLOR AS HEADER
    col1, col2 = st.columns(2)
    col1.button("New Registration", key="login_reg", on_click=lambda: set_auth_view("admin_register"))
    col2.button("Forgot Password?", key="login_fp", on_click=lambda: set_auth_view("forgot_password"))

def render_admin_dashboard_home_view():
    st.session_state['current_page'] = 'visitor_dashboard'
    st.rerun()

def render_forgot_password_view():
    conn = get_fast_connection()
    if 'reset_uid' not in st.session_state:
        with st.form("fp_form"):
            email = st.text_input("Enter Email").lower()
            submit = st.form_submit_button("Verify Email", type="primary")
            if submit:
                user = get_admin_by_email(conn, email)
                if user:
                    st.session_state['reset_uid'] = user['id']
                    st.rerun()
                else:
                    st.error("Email not found")
    else:
        with st.form("pw_reset"):
            p1 = st.text_input("New Password", type="password")
            p2 = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Reset", type="primary")
            if submit and p1 == p2:
                update_admin_password_directly(conn, st.session_state['reset_uid'], hash_password(p1))
                del st.session_state['reset_uid']
                set_auth_view("admin_login")

    st.button("Back to Login", key="fp_back", on_click=lambda: set_auth_view("admin_login"))

# ==============================================================================
# 5. MAIN PAGE + HEADER (UPDATED TO MATCH YOUR REFERENCE IMAGE)
# ==============================================================================

def render_visitor_login_page():

    if 'visitor_auth_view' not in st.session_state:
        st.session_state['visitor_auth_view'] = "admin_login"

    view = st.session_state['visitor_auth_view']

    header_titles = {
        "admin_login": "ZODOPT MEETEASE",
        "admin_register": "ZODOPT MEETEASE",
        "forgot_password": "ZODOPT MEETEASE",
        "admin_dashboard_home": "ZODOPT MEETEASE",
    }
    title = header_titles.get(view, "ZODOPT")

    # ------------------ HEADER CSS (LOOKS LIKE YOUR IMAGE) ------------------
    st.markdown(f"""
    <style>

    .stApp > header {{visibility: hidden;}}

    .header-box {{
        background: {HEADER_GRADIENT};
        width: 100vw;
        margin-left: calc(50% - 50vw);
        padding: 26px 45px;
        border-radius: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0px 4px 22px rgba(0,0,0,0.25);
    }}

    .header-title {{
        color: white;
        font-size: 38px;
        font-weight: 800;
        letter-spacing: 1px;
    }}

    .header-logo {{
        height: 55px;
    }}

    /* Gradient Buttons (Forgot / Registration) */
    .stButton > button {{
        background: {HEADER_GRADIENT} !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        width: 100%;
    }}
    .stButton > button:hover {{
        opacity: 0.92;
    }}

    </style>
    """, unsafe_allow_html=True)

    # ------------------ HEADER RENDER ------------------
    if os.path.exists(LOGO_PATH):
        st.markdown(
            f"""
            <div class="header-box">
                <div class="header-title">{title}</div>
                <img src="{LOGO_PATH}" class="header-logo" />
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="header-box">
                <div class="header-title">{title}</div>
                <div style="color:white;font-size:22px;">zodopt</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ------------------ ROUTER ------------------
    if view == "admin_login":
        render_existing_admin_login_view()
    elif view == "admin_register":
        render_admin_register_view()
    elif view == "forgot_password":
        render_forgot_password_view()
    elif view == "admin_dashboard_home":
        render_admin_dashboard_home_view()

# ==============================================================================
# START APP
# ==============================================================================
if __name__ == "__main__":
    render_visitor_login_page()
