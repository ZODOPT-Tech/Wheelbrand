import streamlit as st
import os
import mysql.connector
import bcrypt
import boto3
import json
import smtplib
import random
import string
from email.mime.text import MIMEText
from time import sleep
from typing import Dict, Any, Optional

# ======================================================
# CONFIG
# ======================================================
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
LOGO_PATH = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #4B2ECF, #7A42FF)"
MIN_PASSWORD_LENGTH = 8
DEFAULT_DB_PORT = 3306

# ======================================================
# AWS SECRET MANAGER
# ======================================================
@st.cache_resource
def get_db_credentials() -> Dict[str, str]:
    try:
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        return json.loads(resp["SecretString"])
    except:
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

# ======================================================
# SECURITY
# ======================================================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()

def check_password(password: str, hash_val: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash_val.encode())

def set_auth_view(view: str):
    st.session_state["visitor_auth_view"] = view
    sleep(0.05)
    st.rerun()

# ======================================================
# SMTP EMAIL FUNCTION
# ======================================================
def send_email(to_email: str, subject: str, body: str) -> bool:
    creds = get_db_credentials()
    try:
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = creds["SMTP_USER"]
        msg["To"] = to_email

        if int(creds["SMTP_PORT"]) == 465:
            server = smtplib.SMTP_SSL(creds["SMTP_HOST"], int(creds["SMTP_PORT"]))
        else:
            server = smtplib.SMTP(creds["SMTP_HOST"], int(creds["SMTP_PORT"]))
            server.starttls()

        server.login(creds["SMTP_USER"], creds["SMTP_PASSWORD"])
        server.sendmail(creds["SMTP_USER"], to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email send failed: {e}")
        return False

# ======================================================
# DB FUNCTIONS
# ======================================================
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
            INSERT INTO admin_users (company_id,name,email,password_hash,is_active)
            VALUES (%s,%s,%s,%s,1)
        """, (cid, aname, email, hashed))
        conn.commit()

        # Send welcome email
        subject = "Welcome to ZODOPT"
        body = f"Hello {aname},\n\nYour admin account has been created successfully.\n\nEmail: {email}"
        send_email(email, subject, body)

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

def create_forgot_password_code(conn, admin_id) -> str:
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO admin_forgot_password (admin_id, verification_code)
        VALUES (%s, %s)
    """, (admin_id, code))
    conn.commit()
    return code

def verify_forgot_code(conn, admin_id, code) -> bool:
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM admin_forgot_password
        WHERE admin_id=%s AND verification_code=%s AND is_used=FALSE
        ORDER BY created_at DESC LIMIT 1
    """, (admin_id, code))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE admin_forgot_password SET is_used=TRUE WHERE id=%s", (row['id'],))
        conn.commit()
        return True
    return False

# ======================================================
# UI COMPONENTS
# ======================================================
def render_admin_register_view():
    conn = get_fast_connection()
    with st.form("reg_form"):
        cname = st.text_input("Company Name")
        aname = st.text_input("Admin Name")
        email = st.text_input("Email").lower()
        p1 = st.text_input("Password", type="password")
        p2 = st.text_input("Confirm Password", type="password")
        sub = st.form_submit_button("Register")

        if sub:
            if p1 == p2 and len(p1) >= MIN_PASSWORD_LENGTH:
                if create_company_and_admin(conn, cname, aname, email, hash_password(p1)):
                    st.success("Registration successful. Welcome email sent!")
                    set_auth_view("admin_login")
                else:
                    st.error("Registration failed. Email might already exist.")
            else:
                st.error(f"Passwords must match and be at least {MIN_PASSWORD_LENGTH} characters.")

    if st.button("Back to Login", use_container_width=True):
        set_auth_view("admin_login")


def render_existing_admin_login_view():
    conn = get_fast_connection()
    with st.form("login_form"):
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
                    code = create_forgot_password_code(conn, user["id"])
                    send_email(email, "ZODOPT Password Reset Code", f"Your verification code is: {code}")
                    st.session_state["reset_uid"] = user["id"]
                    st.session_state["verified"] = False
                    st.success("Verification code sent to your email.")
                    st.rerun()
                else:
                    st.error("Email not found")
    else:
        if not st.session_state.get("verified"):
            with st.form("verify_code_form"):
                code_input = st.text_input("Enter 6-digit Verification Code").upper()
                sub = st.form_submit_button("Verify Code")
                if sub:
                    if verify_forgot_code(conn, st.session_state["reset_uid"], code_input):
                        st.session_state["verified"] = True
                        st.success("Code verified! You can now reset your password.")
                        st.rerun()
                    else:
                        st.error("Invalid or expired code.")
        else:
            with st.form("rp_form"):
                p1 = st.text_input("New Password", type="password")
                p2 = st.text_input("Confirm Password", type="password")
                sub = st.form_submit_button("Reset Password")
                if sub and p1 == p2 and len(p1) >= MIN_PASSWORD_LENGTH:
                    update_admin_password_directly(conn, st.session_state["reset_uid"], hash_password(p1))
                    del st.session_state["reset_uid"]
                    del st.session_state["verified"]
                    st.success("Password updated successfully!")
                    set_auth_view("admin_login")
                else:
                    st.warning(f"Passwords must match and be at least {MIN_PASSWORD_LENGTH} characters.")

    if st.button("Back to Login", use_container_width=True):
        set_auth_view("admin_login")


# ======================================================
# MAIN PAGE + HEADER
# ======================================================
def render_visitor_login_page():
    if "visitor_auth_view" not in st.session_state:
        st.session_state["visitor_auth_view"] = "admin_login"

    view = st.session_state["visitor_auth_view"]

    # ---------------- Dynamic Header Title ----------------
    title_map = {
        "admin_register": "NEW ADMIN REGISTRATION",
        "forgot_password": "RESET PASSWORD",
        "admin_login": "ADMIN LOGIN",
        "admin_dashboard_home": "ZODOPT MEETEASE"
    }
    title = title_map.get(view, "ZODOPT MEETEASE")

    # ---------------- Header CSS ----------------
    st.markdown(f"""
    <style>
    .stApp > header {{visibility: hidden;}}
    .header-box {{
        background: {HEADER_GRADIENT};
        padding: 26px 45px;
        border-radius: 12px;
        max-width: 1600px;
        width: 100%;
        margin: 0 auto 35px auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0px 4px 22px rgba(0,0,0,0.25);
    }}
    .header-title {{
        font-size: 38px;
        font-weight: 800;
        color: white;
        margin: 0;
    }}
    .header-logo {{
        height: 55px;
        object-fit: contain;
    }}
    .stButton > button, .stForm button[type="submit"] {{
        background: {HEADER_GRADIENT} !important;
        color: white !important;
        border-radius: 12px !important;
        width: 100% !important;
        padding: 16px 0 !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        border: none !important;
    }}
    .stButton > button:hover, .stForm button[type="submit"]:hover {{
        opacity: 0.92 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ---------------- HEADER ----------------
    st.markdown(f"""
    <div class="header-box">
        <div class="header-title">{title}</div>
        <img src="{LOGO_PATH}" class="header-logo">
    </div>
    """, unsafe_allow_html=True)

    # ---------------- ROUTING ----------------
    if view == "admin_login":
        render_existing_admin_login_view()
    elif view == "admin_register":
        render_admin_register_view()
    elif view == "forgot_password":
        render_forgot_password_view()
    elif view == "admin_dashboard_home":
        render_admin_dashboard_home_view()


# ======================================================
# START APP
# ======================================================
if __name__ == "__main__":
    render_visitor_login_page()
