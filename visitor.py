import streamlit as st
from PIL import Image
import mysql.connector
import re
import boto3
import json
from io import BytesIO
import base64
from datetime import datetime
import bcrypt

# Optional: drawable signature
try:
    from streamlit_drawable_canvas import st_canvas
    DRAWABLE_AVAILABLE = True
except Exception:
    DRAWABLE_AVAILABLE = False

# ---------------- SETTINGS ----------------
LOGO_PATH = "zodopt.png"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
AWS_REGION = "ap-south-1"
DB_TABLE = "admin"
VISITOR_TABLE = "VISITOR_LOG"

ENABLE_DRAW_SIGNATURE = False  # Set to True if using drawable canvas


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
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    try:
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        creds = json.loads(resp["SecretString"])
        required_keys = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        for k in required_keys:
            if k not in creds:
                st.error(f"Missing AWS secret key: {k}")
                st.stop()
        return creds
    except Exception as e:
        st.error(f"AWS Secret Error: {e}")
        st.stop()


# ---------------- FAST DB CONNECTION ----------------
@st.cache_resource
def get_fast_connection():
    c = get_db_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        port=3306,
        autocommit=True
    )


# ---------------- DB FUNCTIONS ----------------
def email_exists(email):
    conn = get_fast_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM {DB_TABLE} WHERE email=%s LIMIT 1", (email,))
    exists = cur.fetchone() is not None
    cur.close()
    return exists


def create_admin(full, email, pwd):
    if email_exists(email):
        return "Email already exists."

    hashed = make_bcrypt_hash(pwd)
    conn = get_fast_connection()
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO {DB_TABLE}(full_name, email, password_hash, created_at) VALUES (%s, %s, %s, %s)",
        (full, email, hashed, datetime.utcnow()),
    )
    cur.close()
    return "SUCCESS"


def verify_admin(email, pwd):
    conn = get_fast_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT password_hash FROM {DB_TABLE} WHERE email=%s LIMIT 1", (email,))
    row = cur.fetchone()
    cur.close()

    if not row:
        return "Email not found."

    return "SUCCESS" if check_bcrypt(pwd, row[0]) else "Incorrect password."


def update_password(email, newpwd):
    hashed = make_bcrypt_hash(newpwd)
    conn = get_fast_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE {DB_TABLE} SET password_hash=%s WHERE email=%s", (hashed, email))
    cur.close()
    return "SUCCESS"


# ---------------- VISITOR INSERT ----------------
def insert_visitor(payload: dict):
    conn = get_fast_connection()
    cur = conn.cursor()
    cols = ",".join(payload.keys())
    placeholders = ",".join(["%s"] * len(payload))
    sql = f"INSERT INTO {VISITOR_TABLE} ({cols}) VALUES ({placeholders})"
    cur.execute(sql, tuple(payload.values()))
    inserted_id = cur.lastrowid
    cur.close()
    return inserted_id


# ---------------- IMAGE BASE64 ----------------
def file_to_base64(file) -> str:
    if file is None:
        return None
    data = file.read()
    try:
        img = Image.open(BytesIO(data))
        fmt = img.format or "PNG"
        buffered = BytesIO()
        img.save(buffered, format=fmt)
        encoded = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/{fmt.lower()};base64,{encoded}"
    except:
        return "data:application/octet-stream;base64," + base64.b64encode(data).decode()


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


# ---------------- MAIN ENTRY ----------------
def visitor_main(navigate_to):
    mode = st.session_state.get("auth_mode", "login")

    page_title = {
        "login": "Admin Login",
        "register": "Admin Registration",
        "forgot": "Reset Password",
        "dashboard": "Visitor Registration"
    }.get(mode, "Admin Area")

    st.markdown(f"""
    <div style="width:100%;padding:20px 30px;border-radius:15px;
        background: linear-gradient(90deg,#1e62ff,#8a2eff);color:white;
        display:flex;justify-content:space-between;align-items:center;">
        <div style="font-size:28px;font-weight:700;">{page_title}</div>
        <img src="data:image/png;base64,{logo_b64}" style="height:60px;">
    </div>
    """, unsafe_allow_html=True)

    if mode == "login":
        show_login(navigate_to)
    elif mode == "register":
        show_register(navigate_to)
    elif mode == "forgot":
        show_forgot(navigate_to)
    elif mode == "dashboard":
        show_visitor_flow(navigate_to)


# ---------------- LOGIN ----------------
def show_login(navigate_to):
    email = st.text_input("Email")
    pwd = st.text_input("Password", type="password")

    if st.button("Sign In →", use_container_width=True):
        res = verify_admin(email.lower(), pwd)
        if res == "SUCCESS":
            st.session_state["auth_mode"] = "dashboard"
            st.session_state["admin_logged"] = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error(res)

    col1, col2 = st.columns(2)
    if col1.button("New Registration"):
        st.session_state["auth_mode"] = "register"
        st.rerun()

    if col2.button("Forgot Password?"):
        st.session_state["auth_mode"] = "forgot"
        st.rerun()


# ---------------- ADMIN REGISTRATION ----------------
def show_register(navigate_to):
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
                st.success("Admin registered! Please login.")
                st.session_state["auth_mode"] = "login"
                st.rerun()
            else:
                st.error(result)


# ---------------- FORGOT PASSWORD ----------------
def show_forgot(navigate_to):
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
            st.success("Password updated!")
            st.session_state["auth_mode"] = "login"
            st.rerun()


# ---------------- VISITOR FORM (3 STEPS) ----------------
def show_visitor_flow(navigate_to):
    if "visitor_step" not in st.session_state:
        init_visitor_state()

    step = st.session_state["visitor_step"]
    st.write(f"### Step {step} of 3")

    if step == 1:
        step_primary()
    elif step == 2:
        step_secondary()
    elif step == 3:
        step_identity()


def init_visitor_state():
    st.session_state["visitor_step"] = 1
    fields = [
        "v_name","v_phone","v_email","v_host","v_company","v_visit_type","v_department",
        "v_designation","v_org_address","v_city","v_state","v_postal_code","v_country",
        "v_gender","v_purpose"
    ]
    for f in fields:
        st.session_state[f] = ""

    st.session_state["v_bags"] = 0
    st.session_state["v_documents"] = 0
    st.session_state["v_laptop"] = 0
    st.session_state["v_power_bank"] = 0
    st.session_state["v_signature_b64"] = None
    st.session_state["v_photo_b64"] = None


# ---------- STEP 1 ----------
def step_primary():
    st.text_input("Full name", key="v_name")
    st.text_input("Phone", key="v_phone")
    st.text_input("Email", key="v_email")
    st.text_input("Host (Person to meet)", key="v_host")

    col1, col2 = st.columns(2)
    if col1.button("Reset"):
        init_visitor_state()
        st.rerun()

    if col2.button("Next →"):
        if not st.session_state["v_name"]:
            st.error("Name required.")
        elif not st.session_state["v_phone"]:
            st.error("Phone required.")
        elif not is_valid_email(st.session_state["v_email"]):
            st.error("Valid email required.")
        elif not st.session_state["v_host"]:
            st.error("Host required.")
        else:
            st.session_state["visitor_step"] = 2
            st.rerun()


# ---------- STEP 2 ----------
def step_secondary():
    st.selectbox("Visit Type", ["","Business","Personal","Delivery","Interview"], key="v_visit_type")
    st.text_input("From Company", key="v_company")
    st.text_input("Department", key="v_department")
    st.text_input("Designation", key="v_designation")
    st.text_area("Organization Address", key="v_org_address")

    col1, col2, col3 = st.columns([2,1,1])
    col1.text_input("City", key="v_city")
    col2.text_input("State", key="v_state")
    col3.text_input("Postal Code", key="v_postal_code")

    st.selectbox("Country", ["","India","USA","UK","Other"], key="v_country")

    st.radio("Gender", ["","Male","Female","Others"], key="v_gender")
    st.selectbox("Purpose", ["","Meeting","Delivery","Interview","Maintenance","Other"], key="v_purpose")

    belongings = st.multiselect("Belongings", ["Bags","Documents","Laptop","Power Bank"])
    st.session_state["v_bags"] = 1 if "Bags" in belongings else 0
    st.session_state["v_documents"] = 1 if "Documents" in belongings else 0
    st.session_state["v_laptop"] = 1 if "Laptop" in belongings else 0
    st.session_state["v_power_bank"] = 1 if "Power Bank" in belongings else 0

    col1, col2 = st.columns(2)
    if col1.button("← Previous"):
        st.session_state["visitor_step"] = 1
        st.rerun()

    if col2.button("Next →"):
        st.session_state["visitor_step"] = 3
        st.rerun()


# ---------- STEP 3 ----------
def step_identity():
    st.write("Upload Photo and Signature")

    photo = st.file_uploader("Photo", type=["png","jpg","jpeg"])
    signature = st.file_uploader("Signature", type=["png","jpg","jpeg"])

    if photo:
        st.session_state["v_photo_b64"] = file_to_base64(photo)
    if signature:
        st.session_state["v_signature_b64"] = file_to_base64(signature)

    if ENABLE_DRAW_SIGNATURE and DRAWABLE_AVAILABLE:
        st.write("Or draw signature:")
        canvas = st_canvas(
            stroke_width=2,
            stroke_color="#000000",
            background_color="#FFFFFF",
            height=200,
            width=500,
            drawing_mode="freedraw",
            key="canvas_sig"
        )
        if canvas.image_data is not None:
            img = Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA').convert("RGB")
            buf = BytesIO()
            img.save(buf, format="PNG")
            encoded = base64.b64encode(buf.getvalue()).decode()
            st.session_state["v_signature_b64"] = f"data:image/png;base64,{encoded}"

    col1, col2 = st.columns(2)
    if col1.button("← Previous"):
        st.session_state["visitor_step"] = 2
        st.rerun()

    if col2.button("Submit Registration"):
        payload = {
            "name": st.session_state["v_name"],
            "phone": st.session_state["v_phone"],
            "email": st.session_state["v_email"],
            "host": st.session_state["v_host"],
            "time_in": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "checked_in",

            "company": st.session_state["v_company"],
            "visit_type": st.session_state["v_visit_type"],
            "department": st.session_state["v_department"],
            "designation": st.session_state["v_designation"],
            "org_address": st.session_state["v_org_address"],
            "city": st.session_state["v_city"],
            "state": st.session_state["v_state"],
            "postal_code": st.session_state["v_postal_code"],
            "country": st.session_state["v_country"],
            "gender": st.session_state["v_gender"],
            "purpose": st.session_state["v_purpose"],

            "bags": st.session_state["v_bags"],
            "documents": st.session_state["v_documents"],
            "laptop": st.session_state["v_laptop"],
            "power_bank": st.session_state["v_power_bank"],

            "signature_mock": st.session_state["v_signature_b64"],
            "photo_base64": st.session_state["v_photo_b64"]
        }

        try:
            visitor_id = insert_visitor(payload)
            st.success(f"Visitor Registered Successfully (Log ID: {visitor_id})")

            init_visitor_state()
            st.session_state["visitor_step"] = 1
            st.rerun()

        except Exception as e:
            st.error(f"Error saving visitor: {e}")
