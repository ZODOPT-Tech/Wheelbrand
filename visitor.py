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

st.set_page_config(page_title="ZODOPT Admin", layout="wide")

# ---------------- CONFIG ----------------
# Local path to logo (use the path from your runtime / repository)
LOGO_PATH = "/mnt/data/zodopt.png"   # <--- local path from conversation history

AWS_SECRET_NAME = "wheelbrand"
AWS_REGION = "ap-south-1"  # Mumbai

DB_TABLE = "admin"  # table name requested by user

# ---------------- HELPERS ----------------
def is_valid_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def make_bcrypt_hash(plain_password: str) -> str:
    """Return bcrypt hash as UTF-8 string suitable for storing in VARCHAR(255)."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def check_bcrypt_password(plain_password: str, hashed_password: str) -> bool:
    """Verify bcrypt password. hashed_password is stored as UTF-8 string."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False

# ---------------- AWS SECRETS (key=value format) ----------------
@st.cache_resource
def get_db_credentials():
    """
    Fetch DB credentials from AWS Secrets Manager.
    Expects secret's SecretString to be key=value lines like:
        DB_HOST=...
        DB_NAME=...
        DB_USER=...
        DB_PASSWORD=...
    """
    try:
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=AWS_REGION)
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        secret_string = resp.get("SecretString")
        if not secret_string:
            st.error("SecretString not found in Secrets Manager response.")
            st.stop()

        creds = {}
        # Parse key=value lines (supports newline or comma separated)
        for part in re.split(r"[\r\n]+", secret_string):
            if not part.strip():
                continue
            if "=" in part:
                k, v = part.split("=", 1)
                creds[k.strip()] = v.strip()

        # Accept also JSON format (backwards compatibility)
        if not creds:
            try:
                creds_json = json.loads(secret_string)
                creds.update(creds_json)
            except Exception:
                pass

        # Basic validation
        required_keys = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
        for key in required_keys:
            if key not in creds:
                st.error(f"Missing '{key}' in secret '{AWS_SECRET_NAME}'. Please store DB_HOST, DB_NAME, DB_USER, DB_PASSWORD.")
                st.stop()
        return creds

    except ClientError as e:
        st.error(f"Could not retrieve secret '{AWS_SECRET_NAME}': {e}")
        st.stop()

def get_connection():
    creds = get_db_credentials()
    return mysql.connector.connect(
        host=creds["DB_HOST"],
        user=creds["DB_USER"],
        password=creds["DB_PASSWORD"],
        database=creds["DB_NAME"],
        port=int(creds.get("DB_PORT", 3306))
    )

# ---------------- DB OPERATIONS ----------------
def email_exists(email: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM {DB_TABLE} WHERE email = %s LIMIT 1", (email,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def create_admin(full_name: str, email: str, password: str) -> str:
    if email_exists(email):
        return "Email already registered."
    hashed = make_bcrypt_hash(password)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO {DB_TABLE} (full_name, email, password_hash, created_at) VALUES (%s, %s, %s, %s)",
        (full_name, email, hashed, datetime.utcnow())
    )
    conn.commit()
    cur.close()
    conn.close()
    return "SUCCESS"

def verify_admin(email: str, password: str) -> str:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT password_hash FROM {DB_TABLE} WHERE email = %s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return "Email not found."
    stored_hash = row[0]
    if check_bcrypt_password(password, stored_hash):
        return "SUCCESS"
    return "Incorrect password."

def update_password(email: str, new_password: str) -> str:
    if not email_exists(email):
        return "Email not found."
    hashed = make_bcrypt_hash(new_password)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE {DB_TABLE} SET password_hash = %s WHERE email = %s", (hashed, email))
    conn.commit()
    cur.close()
    conn.close()
    return "SUCCESS"

# ---------------- LOGO (base64 embed) ----------------
def load_logo_base64(path: str) -> str:
    try:
        img = Image.open(path)
        buf = BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return b64
    except Exception:
        return ""

logo_b64 = load_logo_base64(LOGO_PATH)

# ---------------- FRONTEND STYLE ----------------
st.markdown(
    """
    <style>
    .header {
        width: 100%;
        padding: 20px 30px;
        border-radius: 18px;
        background: linear-gradient(90deg, #1e62ff, #8a2eff);
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 25px;
    }
    .header-title { font-size: 28px; font-weight: 700; }
    .card {
        background-color: white;
        padding: 28px;
        border-radius: 14px;
        box-shadow: 0px 8px 20px rgba(0,0,0,0.06);
    }
    .muted { color:#666; font-size:13px; }
    .btn-primary {
        background: linear-gradient(90deg,#1e62ff,#8a2eff);
        color: white;
        padding: 10px 18px;
        border-radius: 10px;
        border: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- HEADER ----------------
logo_img_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:62px;"/>' if logo_b64 else ""
st.markdown(f"""
    <div class="header">
        <div class="header-title">ZODOPT MEETEASE</div>
        <div>{logo_img_html}</div>
    </div>
""", unsafe_allow_html=True)

# ---------------- NAV / PAGES ----------------
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

page = st.radio("", ("Signup (Admin)", "Login", "Forgot Password"), horizontal=True)

# ---------------- SIGNUP ----------------
if page == "Signup (Admin)":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Create Admin Account")
    full_name = st.text_input("Full name")
    email = st.text_input("Email address")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm password", type="password")

    if st.button("Create Admin Account", key="create_admin"):
        # validations
        if not full_name.strip():
            st.error("Full name is required.")
        elif not is_valid_email(email):
            st.error("Enter a valid email address.")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters.")
        elif password != confirm:
            st.error("Passwords do not match.")
        else:
            try:
                res = create_admin(full_name.strip(), email.strip().lower(), password)
                if res == "SUCCESS":
                    st.success("Admin registered successfully. Please login.")
                else:
                    st.error(res)
            except Exception as e:
                st.error(f"Error creating admin: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- LOGIN ----------------
elif page == "Login":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Admin Login")
    email = st.text_input("Email address", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login", key="login_btn"):
        if not is_valid_email(email):
            st.error("Enter a valid email address.")
        elif not password:
            st.error("Enter password.")
        else:
            try:
                result = verify_admin(email.strip().lower(), password)
                if result == "SUCCESS":
                    st.session_state["admin_logged_in"] = True
                    # User selected option C earlier: show simple success page
                    st.success("Login successful!")
                    st.markdown("<br/>", unsafe_allow_html=True)
                    st.info("You are now logged in as admin.")
                else:
                    st.error(result)
            except Exception as e:
                st.error(f"Login error: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- FORGOT PASSWORD ----------------
elif page == "Forgot Password":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Forgot Password / Reset")
    fp_email = st.text_input("Enter your registered admin email", key="fp_email")
    if st.button("Find account", key="fp_find"):
        if not is_valid_email(fp_email):
            st.error("Enter a valid email.")
        else:
            try:
                if email_exists(fp_email.strip().lower()):
                    st.success("Email found. Enter new password below.")
                    new_pw = st.text_input("New password", type="password", key="fp_new")
                    confirm_pw = st.text_input("Confirm new password", type="password", key="fp_confirm")
                    if st.button("Update password", key="fp_update"):
                        if not new_pw or not confirm_pw:
                            st.error("Enter and confirm the new password.")
                        elif new_pw != confirm_pw:
                            st.error("Passwords do not match.")
                        elif len(new_pw) < 6:
                            st.error("Password must be at least 6 characters.")
                        else:
                            upd = update_password(fp_email.strip().lower(), new_pw)
                            if upd == "SUCCESS":
                                st.success("Password updated. Please login with your new password.")
                            else:
                                st.error(upd)
                else:
                    st.error("Email not found in system.")
            except Exception as e:
                st.error(f"Error: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- SHOW LOGIN STATE ----------------
st.markdown("<div style='margin-top:18px'></div>", unsafe_allow_html=True)
if st.session_state.get("admin_logged_in"):
    st.success("Admin is logged in (session active).")

# ---------------- END ----------------
