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
st.set_page_config(page_title="ZODOPT Admin", layout="wide")

LOGO_PATH = "zodopt.png"
AWS_SECRET_NAME = "wheelbrand"
AWS_REGION = "ap-south-1"
DB_TABLE = "admin"

# Initialize session state for login status
if "admin_logged" not in st.session_state:
    st.session_state["admin_logged"] = False

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

# ---------------- AWS SECRET MANAGER & DB CONNECTION (No changes here, it's correct) ----------------
# The get_db_credentials and get_connection functions remain the same as they are correct.
@st.cache_resource
def get_db_credentials():
    session = boto3.session.Session()
    client = session.client("secretsmanager", region_name=AWS_REGION)
    try:
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        secret_string = resp.get("SecretString")
        creds = {}
        if "=" in secret_string:
            for line in re.split(r"[\r\n]+", secret_string):
                if "=" in line:
                    k, v = line.split("=", 1)
                    creds[k.strip()] = v.strip()
        else:
            creds.update(json.loads(secret_string))

        for k in ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]:
            if k not in creds:
                st.error(f"Missing {k} in AWS secret.")
                st.stop()
        return creds
    except ClientError as e:
        st.error(f"AWS Error: {e}")
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

# ---------------- DB OPS (No changes here, it's correct) ----------------
# email_exists, create_admin, verify_admin, update_password functions remain the same.

# ---------------- LOGO (No changes here, it's correct) ----------------
def load_logo(path):
    try:
        img = Image.open(path)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except:
        return ""
logo_b64 = load_logo(LOGO_PATH)

# ---------------- STYLES (No changes here, it's correct) ----------------
st.markdown("""
<style>
.card {
    background: white;
    padding: 30px;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)

# ---------------- AUTHENTICATED VIEW ----------------
def show_admin_dashboard():
    """Content displayed after successful login."""
    st.sidebar.title(f"Welcome, Admin!")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"admin_logged": False}))
    st.title("Admin Dashboard 📊")
    st.success("You are successfully logged in.")
    # Add your main admin content here (e.g., reports, user management forms)
    st.write("This is where your secure admin content goes.")

# ---------------- AUTHENTICATION VIEW ----------------
def show_authentication_forms():
    """Login, Registration, and Forgot Password forms."""
    
    st.image(f"data:image/png;base64,{logo_b64}", width=140)
    st.title("ZODOPT Admin Portal")

    # Use horizontal layout for menu
    col1, col2, col3 = st.columns(3)
    with col1:
        login_btn = st.button("Login", use_container_width=True)
    with col2:
        reg_btn = st.button("New Registration", use_container_width=True)
    with col3:
        forgot_btn = st.button("Forgot Password", use_container_width=True)

    # Determine which form to show based on button clicks or default
    if login_btn or ("auth_mode" not in st.session_state and not reg_btn and not forgot_btn):
        st.session_state["auth_mode"] = "Login"
    elif reg_btn:
        st.session_state["auth_mode"] = "New Registration"
    elif forgot_btn:
        st.session_state["auth_mode"] = "Forgot Password"

    menu = st.session_state["auth_mode"]

    # --- LOGIN ---
    if menu == "Login":
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Admin Login")

        email = st.text_input("Email", key="login_email")
        pwd = st.text_input("Password", type="password", key="login_pwd")

        if st.button("Login"):
            res = verify_admin(email.lower(), pwd)
            if res == "SUCCESS":
                st.session_state["admin_logged"] = True # Set session state to True on success
                st.session_state["admin_email"] = email.lower() # Store email if needed
                st.success("Login successful! Redirecting to dashboard...")
                st.rerun() # Rerun the script to show the dashboard
            else:
                st.error(res)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- SIGNUP ---
    elif menu == "New Registration":
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Create Admin Account")

        full = st.text_input("Full Name")
        email = st.text_input("Email")
        pwd = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")

        if st.button("Register Admin"):
            if not full:
                st.error("Full name required.")
            elif not is_valid_email(email):
                st.error("Invalid email.")
            elif pwd != confirm:
                st.error("Passwords do not match.")
            else:
                res = create_admin(full, email.lower(), pwd)
                st.success("Admin created! You can now log in.") if res == "SUCCESS" else st.error(res)

        st.markdown("</div>", unsafe_allow_html=True)

    # --- FORGOT PASSWORD ---
    elif menu == "Forgot Password":
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Reset Password")

        email = st.text_input("Registered Email")
        new_pwd = st.text_input("New Password", type="password")
        confirm = st.text_input("Confirm New Password", type="password")

        if st.button("Update Password"):
            if not email_exists(email.lower()):
                st.error("Email not registered.")
            elif new_pwd != confirm:
                st.error("Passwords do not match.")
            else:
                res = update_password(email.lower(), new_pwd)
                st.success("Password updated! You can now log in.") if res == "SUCCESS" else st.error(res)
        
        st.markdown("</div>", unsafe_allow_html=True)


# ---------------- MAIN APPLICATION LOGIC ----------------
if st.session_state["admin_logged"]:
    show_admin_dashboard()
else:
    show_authentication_forms()
