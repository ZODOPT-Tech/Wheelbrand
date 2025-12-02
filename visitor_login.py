import streamlit as st
import os
import mysql.connector
import bcrypt
import boto3
import json
import traceback
from time import sleep
from typing import Dict, Any, Optional

# ==============================================================================
# CONFIG
# ==============================================================================
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

LOGO_PATH = "zodopt.png"
LOGO_PLACEHOLDER_TEXT = "zodopt"

HEADER_GRADIENT = "linear-gradient(90deg, #4B2ECF, #7A42FF)"
MIN_PASSWORD_LENGTH = 8
DEFAULT_DB_PORT = 3306

# ==============================================================================
# AWS SECRET MANAGER
# ==============================================================================
@st.cache_resource
def get_db_credentials() -> Dict[str, str]:
    try:
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        return json.loads(resp["SecretString"])
    except Exception:
        st.error("Could not load DB credentials.")
        st.stop()

@st.cache_resource
def get_fast_connection():
    creds = get_db_credentials()
    try:
        return mysql.connector.connect(
            host=creds["DB_HOST"],
            user=creds["DB_USER"],
            password=creds["DB_PASSWORD"],
            database=creds["DB_NAME"],
            port=DEFAULT_DB_PORT,
            autocommit=True,
        )
    except:
        st.error("Database connection failed.")
        st.stop()

# ==============================================================================
# SECURITY FUNCTIONS
# ==============================================================================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()

def check_password(password: str, hash_val: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hash_val.encode())
    except:
        return False

def set_auth_view(view: str):
    st.session_state["visitor_auth_view"] = view
    sleep(0.05)
    st.rerun()

# ==============================================================================
# DB QUERIES
# ==============================================================================
def get_admin_by_email(conn, email: str):
    q = """
    SELECT au.id, au.password_hash, au.name,
           c.id AS company_id, c.company_name
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

def update_admin_password_directly(conn, uid, new_hash):
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE admin_users SET password_hash=%s WHERE id=%s", (new_hash, uid))
        conn.commit()
        return True
    except:
        conn.rollback()
        return False

# ==============================================================================
# UI FUNCTIONS
# ==============================================================================
def render_admin_register_view():
    conn = get_fast_connection()

    with st.form("reg_form"):
        st.markdown("### New Admin Registration")

        cname = st.text_input("Company Name")
        aname = st.text_input("Admin Name")
        email = st.text_input("Email").lower()
        p1 = st.text_input("Password", type="password")
        p2 = st.text_input("Confirm Password", type="password")

        sub = st.form_submit_button("Register")

        if sub:
            if p1 == p2 and len(p1) >= MIN_PASSWORD_LENGTH:
                if create_company_and_admin(conn, cname, aname, email, hash_password(p1)):
                    st.success("Registration successful.")
                    set_auth_view("admin_login")
            else:
                st.error("Invalid password")

    # ONLY Back to Login (no forgot password)
    if st.button("Back to Login", use_container_width=True):
        set_auth_view("admin_login")


def render_existing_admin_login_view():
    conn = get_fast_connection()

    with st.form("login_form"):
        st.markdown("### Admin Login")

        email = st.text_input("Email").lower()
        pw = st.text_input("Password", type="password")

        sub = st.form_submit_button("Sign In →")

        if sub:
            user = get_admin_by_email(conn, email)
            if user and check_password(pw, user["password_hash"]):
                st.session_state["admin_logged_in"] = True
                st.session_state["admin_id"] = user["id"]
                st.session_state["admin_name"] = user["name"]
                st.session_state["company_name"] = user["company_name"]
                st.session_state["company_id"] = user["company_id"]
                set_auth_view("admin_dashboard_home")
            else:
                st.error("Invalid login")

    c1, c2 = st.columns(2)
    if c1.button("New Registration", use_container_width=True):
        set_auth_view("admin_register")
    if c2.button("Forgot Password?", use_container_width=True):
        set_auth_view("forgot_password")


def render_admin_dashboard_home_view():
    st.session_state["current_page"] = "visitor_dashboard"
    st.rerun()


def render_forgot_password_view():
    conn = get_fast_connection()

    if "reset_uid" not in st.session_state:
        with st.form("fp_form"):
            email = st.text_input("Enter Email").lower()
            sub = st.form_submit_button("Verify Email")

            if sub:
                user = get_admin_by_email(conn, email)
                if user:
                    st.session_state["reset_uid"] = user["id"]
                    st.rerun()
                else:
                    st.error("Email not found")

    else:
        with st.form("rp_form"):
            p1 = st.text_input("New Password", type="password")
            p2 = st.text_input("Confirm Password", type="password")
            sub = st.form_submit_button("Reset Password")

            if sub and p1 == p2:
                update_admin_password_directly(conn, st.session_state["reset_uid"], hash_password(p1))
                del st.session_state["reset_uid"]
                set_auth_view("admin_login")

    if st.button("Back to Login", use_container_width=True):
        set_auth_view("admin_login")

# ==============================================================================
# MAIN PAGE WITH HEADER
# ==============================================================================
def render_visitor_login_page():

    if "visitor_auth_view" not in st.session_state:
        st.session_state["visitor_auth_view"] = "admin_login"

    view = st.session_state["visitor_auth_view"]

    # ---------------- Dynamic Header Title ----------------
    if view == "admin_register":
        title = "NEW ADMIN REGISTRATION"
    elif view == "admin_login":
        title = "ADMIN LOGIN"
    elif view == "forgot_password":
        title = "RESET PASSWORD"
    else:
        title = "ZODOPT MEETEASE"

    # ---------------- Header CSS ----------------
    st.markdown(f"""
    <style>

    .stApp > header {{visibility: hidden;}}

    .header-box {{
        background: {HEADER_GRADIENT};
        padding: 26px 45px;
        border-radius: 12px;
        box-shadow: 0px 4px 22px rgba(0,0,0,0.25);
        max-width: 1600px;
        width: 100%;
        margin: 0 auto 35px auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .header-title {{
        font-size: 38px;
        font-weight: 800;
        color: white;
        margin: 0;
    }}

    .header-logo {{
        height: 55px;
    }}

    /* Wide gradient action buttons */
    .stButton > button {{
        background: {HEADER_GRADIENT} !important;
        color: white !important;
        border-radius: 12px !important;
        width: 100% !important;
        padding: 14px 0 !important;
        font-size: 17px !important;
        font-weight: 600 !important;
        border: none !important;
    }}

    .stButton > button:hover {{
        opacity: 0.92;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ---------------- Render Header ----------------
    logo_html = (
        f'<img src="{LOGO_PATH}" class="header-logo">'
        if os.path.exists(LOGO_PATH)
        else f'<div style="color:white;font-weight:900;font-size:24px;">{LOGO_PLACEHOLDER_TEXT}</div>'
    )

    st.markdown(
        f"""
        <div class="header-box">
            <div class="header-title">{title}</div>
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------- Router ----------------
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
