# visitor.py
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
st.set_page_config(page_title="ZODOPT Admin", layout="centered")

# Use the repo/container-local path for the logo (from conversation history)
LOGO_PATH = "/mnt/data/zodopt.png"

AWS_SECRET_NAME = "wheelbrand"
AWS_REGION = "ap-south-1"  # Mumbai region
DB_TABLE = "admin"

# ---------------- SESSION DEFAULTS ----------------
if "admin_logged" not in st.session_state:
    st.session_state["admin_logged"] = False
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"  # login | register | forgot
if "remember_me" not in st.session_state:
    st.session_state["remember_me"] = False

# ---------------- HELPERS ----------------
def is_valid_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", (email or "").strip()))

def make_bcrypt_hash(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def check_bcrypt(pwd: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pwd.encode(), hashed.encode())
    except Exception:
        return False

# ---------------- AWS SECRET MANAGER ----------------
@st.cache_resource
def get_db_credentials():
    """Fetch DB credentials from AWS Secrets Manager.
    Supports either key=value lines or JSON in SecretString.
    Expected keys: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD (optional DB_PORT)
    """
    try:
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=AWS_REGION)
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        secret_string = resp.get("SecretString", "")
        if not secret_string:
            st.error("SecretString empty for AWS secret.")
            st.stop()

        creds = {}
        # Try parse key=value lines
        for line in re.split(r"[\r\n]+", secret_string):
            if "=" in line:
                k, v = line.split("=", 1)
                creds[k.strip()] = v.strip()
        # Fallback to JSON
        if not creds:
            try:
                creds = json.loads(secret_string)
            except Exception:
                pass

        required = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
        for k in required:
            if k not in creds:
                st.error(f"Missing {k} in AWS secret '{AWS_SECRET_NAME}'.")
                st.stop()

        # optional port
        if "DB_PORT" in creds:
            try:
                creds["DB_PORT"] = int(creds["DB_PORT"])
            except:
                creds["DB_PORT"] = 3306
        else:
            creds["DB_PORT"] = 3306

        return creds
    except ClientError as e:
        st.error(f"AWS Secrets Manager error: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Unexpected error fetching DB creds: {e}")
        st.stop()

def get_connection():
    creds = get_db_credentials()
    return mysql.connector.connect(
        host=creds["DB_HOST"],
        user=creds["DB_USER"],
        password=creds["DB_PASSWORD"],
        database=creds["DB_NAME"],
        port=creds.get("DB_PORT", 3306),
        connection_timeout=5
    )

# ---------------- DB OPERATIONS ----------------
def email_exists(email: str) -> bool:
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT 1 FROM {DB_TABLE} WHERE email = %s LIMIT 1", (email,))
        exists = cur.fetchone() is not None
        cur.close()
        conn.close()
        return exists
    except Exception as e:
        st.error(f"DB error (email_exists): {e}")
        return False

def create_admin(full_name: str, email: str, password: str) -> str:
    try:
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
    except Exception as e:
        return f"DB error creating admin: {e}"

def verify_admin(email: str, password: str) -> str:
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT password_hash FROM {DB_TABLE} WHERE email = %s", (email,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return "Email not found."
        stored_hash = row[0]
        if check_bcrypt(password, stored_hash):
            return "SUCCESS"
        return "Incorrect password."
    except Exception as e:
        return f"DB error verifying admin: {e}"

def update_password(email: str, new_password: str) -> str:
    try:
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
    except Exception as e:
        return f"DB error updating password: {e}"

# ---------------- LOGO / STYLING ----------------
def load_logo_base64(path: str) -> str:
    try:
        img = Image.open(path)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        return ""

logo_b64 = load_logo_base64(LOGO_PATH)

st.markdown(
    """
    <style>
    /* container */
    .auth-card {
        background: #fff;
        padding: 28px 30px;
        border-radius: 14px;
        box-shadow: 0 8px 30px rgba(16,24,40,0.06);
        width: 720px;
        margin: 20px auto;
    }
    /* input labels */
    .field-label { font-size: 16px; font-weight: 600; margin-bottom: 8px; color:#263238; }
    /* remember row */
    .row-between { display:flex; justify-content:space-between; align-items:center; margin-top: 6px; }
    /* forgot text */
    .forgot { color:#1160ff; text-decoration: underline; cursor: pointer; }
    /* sign in button */
    .sign-btn {
        width:100%;
        padding:14px 18px;
        border-radius: 12px;
        border:none;
        font-size:18px;
        font-weight:600;
        color:white;
        background: linear-gradient(90deg,#1e62ff,#b312ff);
        margin-top:18px;
    }
    .small-btn {
        margin-top:12px;
        width:48%;
        padding:10px 12px;
        border-radius:10px;
        font-weight:600;
        border:none;
        cursor:pointer;
    }
    .reg-btn { background:#ffffff; border:1px solid #e6e9ef; color:#333; }
    .fp-btn { background:transparent; color:#1160ff; text-decoration:underline; border:none; }
    /* header */
    .header {
        width:100%;
        padding: 20px 26px;
        border-radius:12px;
        background: linear-gradient(90deg,#1e62ff,#8a2eff);
        color:white;
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin-bottom: 18px;
    }
    .header-title { font-size:22px; font-weight:700; }
    </style>
    """, unsafe_allow_html=True)

# header block (similar to main.py)
st.markdown(f"""
    <div class="header">
        <div class="header-title">ZODOPT MEETEASE</div>
        <div>{f'<img src="data:image/png;base64,{logo_b64}" style="height:48px;">' if logo_b64 else ''}</div>
    </div>
""", unsafe_allow_html=True)

# ---------------- AUTH CARD UI ----------------
def auth_card_ui():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='margin-bottom:8px;'>Sign In</h3>", unsafe_allow_html=True)
    st.write("Please fill in your details")

    # Email
    st.markdown("<div class='field-label'>Email Address</div>", unsafe_allow_html=True)
    email = st.text_input("", placeholder="you@company.com", key="ui_email")

    # Password
    st.markdown("<div style='margin-top:12px' class='field-label'>Password</div>", unsafe_allow_html=True)
    password = st.text_input("", type="password", placeholder="Enter your password", key="ui_password")

    # Remember + forgot row
    col1, col2 = st.columns([1,1])
    with col1:
        remember = st.checkbox("Remember me", key="ui_remember")
    with col2:
        # forgot as a clickable text — we'll not actually use a link but set auth_mode
        if st.button("Forgot password?", key="ui_forgot_link"):
            st.session_state["auth_mode"] = "forgot"
            st.experimental_rerun()

    # Sign in button
    if st.button("Sign In  →", key="ui_signin", help="Sign in as admin"):
        # validations
        if not is_valid_email(email):
            st.error("Enter a valid email address.")
        elif not password:
            st.error("Enter password.")
        else:
            res = verify_admin(email.strip().lower(), password)
            if res == "SUCCESS":
                st.session_state["admin_logged"] = True
                st.session_state["admin_email"] = email.strip().lower()
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error(res)

    # Buttons below sign in: New Registration and Forgot Password (secondary)
    st.write("")  # spacing
    c1, c2 = st.columns(2)
    with c1:
        if st.button("New Registration", key="ui_newreg"):
            st.session_state["auth_mode"] = "register"
            st.experimental_rerun()
    with c2:
        if st.button("Forgot Password", key="ui_fp"):
            st.session_state["auth_mode"] = "forgot"
            st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- REGISTRATION UI ----------------
def registration_ui():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='margin-bottom:8px;'>Create Admin Account</h3>", unsafe_allow_html=True)

    full = st.text_input("Full name", key="reg_full")
    email = st.text_input("Email address", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_pwd")
    confirm = st.text_input("Confirm password", type="password", key="reg_confirm")

    if st.button("Create Admin Account", key="reg_create"):
        if not full.strip():
            st.error("Full name is required.")
        elif not is_valid_email(email):
            st.error("Enter a valid email address.")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters.")
        elif password != confirm:
            st.error("Passwords do not match.")
        else:
            res = create_admin(full.strip(), email.strip().lower(), password)
            if res == "SUCCESS":
                st.success("Admin registered successfully. Please login.")
                st.session_state["auth_mode"] = "login"
                # clear registration fields (optional)
                st.experimental_rerun()
            else:
                st.error(res)

    # Back to login
    if st.button("Back to Sign In", key="reg_back"):
        st.session_state["auth_mode"] = "login"
        st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- FORGOT / RESET UI ----------------
def forgot_ui():
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='margin-bottom:8px;'>Reset Password</h3>", unsafe_allow_html=True)

    email = st.text_input("Registered email", key="fp_email")
    new_pwd = st.text_input("New password", type="password", key="fp_new")
    confirm = st.text_input("Confirm new password", type="password", key="fp_confirm")

    if st.button("Update password", key="fp_update"):
        if not is_valid_email(email):
            st.error("Enter a valid email address.")
        elif new_pwd != confirm:
            st.error("Passwords do not match.")
        elif len(new_pwd) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            res = update_password(email.strip().lower(), new_pwd)
            if res == "SUCCESS":
                st.success("Password updated. Please login with your new password.")
                st.session_state["auth_mode"] = "login"
                st.experimental_rerun()
            else:
                st.error(res)

    if st.button("Back to Sign In", key="fp_back"):
        st.session_state["auth_mode"] = "login"
        st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- AUTHENTICATED DASHBOARD ----------------
def show_admin_dashboard():
    st.sidebar.title("Admin")
    if st.sidebar.button("Logout"):
        st.session_state["admin_logged"] = False
        st.session_state["auth_mode"] = "login"
        st.experimental_rerun()

    st.title("Admin Dashboard")
    st.success(f"Logged in as: {st.session_state.get('admin_email', 'admin')}")
    st.write("This is the admin area — add visitor registration, lists, reports etc. here.")

# ---------------- MAIN RENDER ----------------
def main():
    # If already logged in -> dashboard
    if st.session_state.get("admin_logged"):
        show_admin_dashboard()
        return

    # Not logged in -> show form depending on auth_mode
    mode = st.session_state.get("auth_mode", "login")
    if mode == "login":
        auth_card_ui()
    elif mode == "register":
        registration_ui()
    elif mode == "forgot":
        forgot_ui()

if __name__ == "__main__":
    main()
