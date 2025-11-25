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

# ---------------- DB OPS ----------------
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
        f"INSERT INTO {DB_TABLE} (full_name, email, password_hash, created_at) VALUES (%s,%s,%s,%s)",
        (full, email, hashed, datetime.utcnow())
    )
    conn.commit()
    cur.close()
    conn.close()
    return "SUCCESS"

def verify_admin(email, pwd):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT password_hash FROM {DB_TABLE} WHERE email=%s", (email,))
    rec = cur.fetchone()
    cur.close()
    conn.close()

    if not rec:
        return "Email not found."

    return "SUCCESS" if check_bcrypt(pwd, rec[0]) else "Incorrect password."

def update_password(email, new_pwd):
    if not email_exists(email):
        return "Email not found."

    hashed = make_bcrypt_hash(new_pwd)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE {DB_TABLE} SET password_hash=%s WHERE email=%s", (hashed, email))
    conn.commit()
    cur.close()
    conn.close()
    return "SUCCESS"

# ---------------- LOGO ----------------
def load_logo(path):
    try:
        img = Image.open(path)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except:
        return ""

logo_b64 = load_logo(LOGO_PATH)

# ---------------- STYLES ----------------
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

# -------------- FIRST PAGE ALWAYS LOGIN ----------------
st.image(f"data:image/png;base64,{logo_b64}", width=140)
st.title("ZODOPT Admin Portal")

menu = st.radio("Select Option", ["Login", "New Registration", "Forgot Password"])

# ---------------- LOGIN ----------------
if menu == "Login":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Admin Login")

    email = st.text_input("Email")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        res = verify_admin(email.lower(), pwd)
        if res == "SUCCESS":
            st.session_state["admin_logged"] = True
            st.success("Login successful!")
        else:
            st.error(res)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- SIGNUP ----------------
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
            st.success("Admin created!") if res == "SUCCESS" else st.error(res)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- FORGOT PASSWORD ----------------
elif menu == "Forgot Password":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Reset Password")

    email = st.text_input("Registered Email")

    if st.button("Verify"):
        if email_exists(email.lower()):
            st.success("Email found. Enter new password.")
            new_pwd = st.text_input("New Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")

            if st.button("Update Password"):
                if new_pwd != confirm:
                    st.error("Passwords do not match.")
                else:
                    res = update_password(email.lower(), new_pwd)
                    st.success("Password updated!") if res == "SUCCESS" else st.error(res)
        else:
            st.error("Email not registered.")

    st.markdown("</div>", unsafe_allow_html=True)
