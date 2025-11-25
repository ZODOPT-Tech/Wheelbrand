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

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="ZODOPT Admin Login", layout="wide")

LOGO_PATH = "zodopt.png"
AWS_SECRET_NAME = "wheelbrand"
AWS_REGION = "ap-south-1"
DB_TABLE = "admin"

# Session flags
if "admin_logged" not in st.session_state:
    st.session_state["admin_logged"] = False

if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"

# ---------------- HELPERS ----------------
def is_valid_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def make_bcrypt_hash(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def check_bcrypt(pwd: str, hashed: str) -> bool:
    try: return bcrypt.checkpw(pwd.encode(), hashed.encode())
    except: return False

# ---------------- AWS SECRET MANAGER ----------------
@st.cache_resource
def get_db_credentials():
    session = boto3.session.Session()
    client = session.client("secretsmanager", region_name=AWS_REGION)

    try:
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        secret = resp.get("SecretString")
        creds = {}

        # key=value format
        for line in secret.split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                creds[k.strip()] = v.strip()

        # Validation
        for key in ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]:
            if key not in creds:
                st.error(f"Missing key in secret: {key}")
                st.stop()

        return creds

    except ClientError as e:
        st.error(f"AWS Error: {e}")
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
    res = cur.fetchone()
    cur.close()
    conn.close()
    return res is not None

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

# ---------------- HEADER STYLE ----------------
st.markdown("""
<style>
.header {
    width: 100%;
    padding: 25px 40px;
    border-radius: 25px;
    background: linear-gradient(90deg,#1e62ff,#8a2eff);
    color: white;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.header-title {
    font-size: 34px;
    font-weight: 700;
}
.logo-img { height: 70px; }

.card {
    background: white;
    padding: 40px;
    border-radius: 20px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    max-width: 450px;
    margin: auto;
}

.input-label {
    font-size: 16px;
    font-weight: 600;
}
.sign-btn {
    width: 100%;
    padding: 15px;
    border-radius: 12px;
    font-size: 18px;
    color: white;
    font-weight: 600;
    background: linear-gradient(90deg,#1e62ff,#8a2eff);
}
.small-btn {
    width: 100%;
    padding: 12px;
    border-radius: 10px;
    background: #f0f0f0;
    font-size: 15px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown(f"""
<div class="header">
    <div class="header-title">ZODOPT MEETEASE</div>
    <img src="data:image/png;base64,{logo_b64}" class="logo-img">
</div>
""", unsafe_allow_html=True)

st.write("")

# -------------------------------------------
#                ADMIN DASHBOARD
# -------------------------------------------
def show_admin_dashboard():
    st.title("Admin Dashboard")
    st.success("Logged in successfully.")
    st.write("Secure admin content here...")
    if st.button("Logout"):
        st.session_state["admin_logged"] = False
        st.rerun()

# -------------------------------------------
#                LOGIN FORM
# -------------------------------------------
def show_login():
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.subheader("Admin Login")

    st.markdown("<div class='input-label'>Email</div>", unsafe_allow_html=True)
    email = st.text_input("", placeholder="you@company.com")

    st.markdown("<div class='input-label'>Password</div>", unsafe_allow_html=True)
    pwd = st.text_input("", type="password", placeholder="Enter your password")

    if st.button("Sign In →", use_container_width=True):
        res = verify_admin(email.lower(), pwd)
        if res == "SUCCESS":
            st.session_state["admin_logged"] = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error(res)

    st.write("")
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

# -------------------------------------------
#                REGISTRATION FORM
# -------------------------------------------
def show_register():
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.subheader("New Admin Registration")

    full = st.text_input("Full Name")
    email = st.text_input("Email")
    pwd = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

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
                st.success("Admin registered successfully!")
                st.session_state["auth_mode"] = "login"
                st.rerun()
            else:
                st.error(result)

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------
#             FORGOT PASSWORD FORM
# -------------------------------------------
def show_forgot():
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.subheader("Reset Password")

    email = st.text_input("Registered Email")
    newpwd = st.text_input("New Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Update Password", use_container_width=True):
        if not email_exists(email.lower()):
            st.error("Email not found.")
        elif newpwd != confirm:
            st.error("Passwords do not match.")
        else:
            update_password(email.lower(), newpwd)
            st.success("Password updated successfully!")
            st.session_state["auth_mode"] = "login"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- ROUTING ----------------
if st.session_state["admin_logged"]:
    show_admin_dashboard()

else:
    mode = st.session_state["auth_mode"]

    if mode == "login":
        show_login()
    elif mode == "register":
        show_register()
    elif mode == "forgot":
        show_forgot()
