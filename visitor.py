import streamlit as st
from PIL import Image
import mysql.connector
import re
import boto3
import json
from botocore.exceptions import ClientError
from io import BytesIO
import base64
from datetime import datetime
import bcrypt

# ---------------- SETTINGS ----------------
LOGO_PATH = "zodopt.png"
AWS_SECRET_NAME = "wheelbrand"
AWS_REGION = "ap-south-1"
DB_TABLE = "admin"


# ---------------- HELPERS ----------------
def is_valid_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


def make_bcrypt_hash(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()


def check_bcrypt(pwd: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pwd.encode(), hashed.encode())
    except:
        return False


# ---------------- AWS SECRET MANAGER ----------------
@st.cache_resource
def get_db_credentials():
    session = boto3.session.Session()
    client = session.client("secretsmanager", region_name=AWS_REGION)

    try:
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        secret = resp["SecretString"]
        creds = {}

        for line in secret.split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                creds[k.strip()] = v.strip()

        for key in ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]:
            if key not in creds:
                st.error(f"Missing AWS secret key: {key}")
                st.stop()

        return creds
    except Exception as e:
        st.error(f"AWS Secret Error: {e}")
        st.stop()


def get_connection():
    c = get_db_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        port=3306
    )


# ---------------- DB FUNCTIONS ----------------
def email_exists(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM {DB_TABLE} WHERE email=%s LIMIT 1", (email,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists


def create_admin(full, email, pwd):
    if email_exists(email):
        return "Email already exists."

    hashed = make_bcrypt_hash(pwd)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO {DB_TABLE}(full_name,email,password_hash,created_at) VALUES (%s,%s,%s,%s)",
        (full, email, hashed, datetime.utcnow()),
    )
    conn.commit()
    cur.close()
    conn.close()
    return "SUCCESS"


def verify_admin(email, pwd):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT password_hash FROM {DB_TABLE} WHERE email=%s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return "Email not found."

    return "SUCCESS" if check_bcrypt(pwd, row[0]) else "Incorrect password."


def update_password(email, newpwd):
    hashed = make_bcrypt_hash(newpwd)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE {DB_TABLE} SET password_hash=%s WHERE email=%s", (hashed, email))
    conn.commit()
    cur.close()
    conn.close()
    return "SUCCESS"


# ---------------- LOAD LOGO ----------------
def load_logo(path):
    try:
        img = Image.open(path)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except:
        return ""


logo_b64 = load_logo(LOGO_PATH)


# ---------------- ENTRYPOINT PAGE FUNCTION ----------------
def visitor_main(navigate_to):
    """
    THIS IS THE ENTRY FUNCTION CALLED FROM main.py
    Updates the main header title based on the current auth mode and injects global button styling.
    """
    mode = st.session_state.get("auth_mode", "login")

    # Map the current mode to the desired header title
    header_titles = {
        "login": "Admin Login",
        "register": "Admin Registration",
        "forgot": "Reset Password",
        "dashboard": "Admin Dashboard"
    }
    
    current_title = header_titles.get(mode, "Admin Area")

    # INJECT CUSTOM CSS FOR GRADIENT BUTTONS AND INPUT CONTAINER
    st.markdown(f"""
    <style>
    /* Custom button styling to match header gradient for all st.button elements */
    .stButton>button {{
        background: linear-gradient(90deg, #1e62ff, #8a2eff);
        color: white !important; /* Ensure text color is white for contrast */
        border-radius: 0.5rem; /* Match header/card rounding */
        border: none; /* Remove default border */
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: transform 0.1s ease, box-shadow 0.1s ease;
    }}
    .stButton>button:hover {{
        /* Slight lift effect on hover */
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
    }}
    /* Styling for the main card container */
    .card {{
        background-color: white;
        padding: 2rem;
        border-radius: 25px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin-top: 2rem;
    }}
    /* Styling for Streamlit text input containers to make them white and prominent */
    .stTextInput>div>div>input, .stPasswordInput>div>div>input {{
        background-color: #f0f2f6; /* A slightly off-white for the input fields */
        border-radius: 0.5rem;
        padding: 0.75rem 1rem;
        border: 1px solid #e0e0e0;
    }}
    .stTextInput>label, .stPasswordInput>label {{
        font-weight: bold; /* Make labels stand out */
        color: #333;
    }}
    /* Ensure the Streamlit input container div itself has a transparent background to not interfere */
    .stTextInput>div>div, .stPasswordInput>div>div {{
        background-color: transparent !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # The header now uses the dynamic title
    st.markdown(f"""
    <div class="header" style="
        width:100%;padding:25px 40px;
        border-radius:25px;
        background: linear-gradient(90deg,#1e62ff,#8a2eff);
        color:white;display:flex;justify-content:space-between;align-items:center;">
        <div style="font-size:34px;font-weight:700;">{current_title}</div>
        <img src="data:image/png;base64,{logo_b64}" style="height:70px;">
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    # ROUTING INSIDE visitor.py
    if mode == "login":
        show_login(navigate_to)
    elif mode == "register":
        show_register(navigate_to)
    elif mode == "forgot":
        show_forgot(navigate_to)
    elif mode == "dashboard":
        show_admin_dashboard(navigate_to)


# ---------------- LOGIN FORM ----------------
def show_login(navigate_to):
    # The 'card' div now serves as the main container for the form
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    # Inputs are now directly inside the 'card', with their own styling
    email = st.text_input("Email")
    pwd = st.text_input("Password", type="password")
    
    st.markdown("<br>", unsafe_allow_html=True) # Add some space before the button

    if st.button("Sign In →", use_container_width=True):
        res = verify_admin(email.lower(), pwd)
        if res == "SUCCESS":
            st.session_state["admin_logged"] = True
            st.session_state["auth_mode"] = "dashboard"
            st.success("Login successful!")
            st.rerun()
        else:
            st.error(res)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("New Registration"):
            st.session_state["auth_mode"] = "register"
            st.rerun()

    with col2:
        if st.button("Forgot Password?"):
            st.session_state["auth_mode"] = "forgot"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------- REGISTRATION FORM ----------------
def show_register(navigate_to):
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    full = st.text_input("Full Name")
    email = st.text_input("Email")
    pwd = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")
    
    st.markdown("<br>", unsafe_allow_html=True) # Add some space before the button

    if st.button("Register Admin", use_container_width=True):
        if not full:
            st.error("Full name required.")
        elif not is_valid_email(email):
            st.error("Invalid email.")
        elif pwd != confirm:
            st.error("Passwords do not match.")
        else:
            result = create_admin(full, email.lower(), pwd)
            if result == "SUCCESS":
                st.success("Admin registered!")
                st.session_state["auth_mode"] = "login"
                st.rerun()
            else:
                st.error(result)

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------- FORGOT PASSWORD FORM ----------------
def show_forgot(navigate_to):
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    email = st.text_input("Registered Email")
    newpwd = st.text_input("New Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")
    
    st.markdown("<br>", unsafe_allow_html=True) # Add some space before the button

    if st.button("Update Password", use_container_width=True):
        if not email_exists(email.lower()):
            st.error("Email not found.")
        elif newpwd != confirm:
            st.error("Passwords do not match.")
        else:
            update_password(email.lower(), newpwd)
            st.success("Password updated!")
            st.session_state["auth_mode"] = "login"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------- DASHBOARD ----------------
def show_admin_dashboard(navigate_to):
    st.title("Admin Dashboard")
    st.success("Logged in successfully.")

    if st.button("Logout"):
        st.session_state["auth_mode"] = "login"
        st.session_state["admin_logged"] = False
        st.rerun()
