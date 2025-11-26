# visitor.py
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

# Optional: drawable canvas for signature (install streamlit-drawable-canvas to enable)
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

# Enable the in-app draw signature if drawable canvas is installed and you want it.
ENABLE_DRAW_SIGNATURE = False  # set to True if you installed streamlit-drawable-canvas


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


# ---------------- FAST DB CONNECTION (CACHED) ----------------
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


# ---------------- DB FUNCTIONS (admin) ----------------
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
    cur.execute(
        f"UPDATE {DB_TABLE} SET password_hash=%s WHERE email=%s",
        (hashed, email)
    )
    cur.close()
    return "SUCCESS"


# ---------------- VISITOR DB INSERT ----------------
def insert_visitor(payload: dict):
    """
    payload keys expected to match VISITOR_LOG columns.
    Required: name, phone, email, host, company (optional), visit_type, department, designation,
              org_address, city, state, postal_code, country, gender, purpose,
              bags, documents, laptop, power_bank, signature_mock, photo_base64
    """
    conn = get_fast_connection()
    cur = conn.cursor()
    cols = []
    vals = []
    for k, v in payload.items():
        cols.append(k)
        vals.append(v)
    placeholders = ",".join(["%s"] * len(vals))
    col_list = ",".join(cols)
    sql = f"INSERT INTO {VISITOR_TABLE} ({col_list}) VALUES ({placeholders})"
    cur.execute(sql, tuple(vals))
    inserted_id = cur.lastrowid
    cur.close()
    return inserted_id


# ---------------- UTILS: IMAGE <-> BASE64 ----------------
def file_to_base64(file) -> str:
    """file: UploadedFile from streamlit; returns base64 string (data URI)"""
    if file is None:
        return None
    data = file.read()
    # detect format
    try:
        img = Image.open(BytesIO(data))
        fmt = img.format or "PNG"
        buffered = BytesIO()
        img.save(buffered, format=fmt)
        b64 = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/{fmt.lower()};base64,{b64}"
    except Exception:
        # fallback - store raw base64
        return "data:application/octet-stream;base64," + base64.b64encode(data).decode()


# ---------------- LOGO LOADER ----------------
def load_logo(path):
    try:
        img = Image.open(path)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except:
        return ""


logo_b64 = load_logo(LOGO_PATH)


# ---------------- ENTRYPOINT (replaces dashboard) ----------------
def visitor_main(navigate_to):
    # preserve auth_mode from session_state; default 'login'
    mode = st.session_state.get("auth_mode", "login")

    header_titles = {
        "login": "Admin Login",
        "register": "Admin Registration",
        "forgot": "Reset Password",
        "dashboard": "Register Visitor"
    }
    current_title = header_titles.get(mode, "Admin Area")

    # simple CSS
    st.markdown(f"""
    <style>
    .stButton>button {{
        background: linear-gradient(90deg, #1e62ff, #8a2eff);
        color: white !important;
        border-radius: 0.5rem;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }}
    .card {{ margin-top: 1rem; }}
    .wide {{ max-width: 900px; margin:auto; }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="width:100%;padding:18px 24px;border-radius:12px;
                background: linear-gradient(90deg,#1e62ff,#8a2eff);
                color:white;display:flex;justify-content:space-between;align-items:center;">
        <div style="font-size:26px;font-weight:700;">{current_title}</div>
        <img src="data:image/png;base64,{logo_b64}" style="height:54px;">
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    # route
    if mode == "login":
        show_login(navigate_to)
    elif mode == "register":
        show_register(navigate_to)
    elif mode == "forgot":
        show_forgot(navigate_to)
    elif mode == "dashboard":
        # Instead of a complex dashboard, we go straight to visitor registration flow
        show_visitor_flow(navigate_to)


# ---------------- LOGIN / REGISTER / FORGOT (same as before) ----------------
def show_login(navigate_to):
    st.markdown("<div class='card wide'>", unsafe_allow_html=True)
    email = st.text_input("Email")
    pwd = st.text_input("Password", type="password")
    if st.button("Sign In →", use_container_width=True):
        res = verify_admin(email.lower(), pwd)
        if res == "SUCCESS":
            st.session_state["admin_logged"] = True
            st.session_state["auth_mode"] = "dashboard"
            st.success("Login successful! Opening Visitor Registration...")
            st.experimental_rerun()
        else:
            st.error(res)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Registration"):
            st.session_state["auth_mode"] = "register"
            st.experimental_rerun()
    with col2:
        if st.button("Forgot Password?"):
            st.session_state["auth_mode"] = "forgot"
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def show_register(navigate_to):
    st.markdown("<div class='card wide'>", unsafe_allow_html=True)
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
                st.experimental_rerun()
            else:
                st.error(result)
    st.markdown("</div>", unsafe_allow_html=True)


def show_forgot(navigate_to):
    st.markdown("<div class='card wide'>", unsafe_allow_html=True)
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
            st.success("Password updated! Please login.")
            st.session_state["auth_mode"] = "login"
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------- VISITOR MULTI-STEP FLOW (PRIMARY -> SECONDARY -> IDENTITY) ----------------
def show_visitor_flow(navigate_to):
    # initialize step
    if "visitor_step" not in st.session_state:
        st.session_state["visitor_step"] = 1
        # form data
        st.session_state.setdefault("v_name", "")
        st.session_state.setdefault("v_phone", "")
        st.session_state.setdefault("v_email", "")
        st.session_state.setdefault("v_host", "")
        st.session_state.setdefault("v_company", "")
        st.session_state.setdefault("v_visit_type", "")
        st.session_state.setdefault("v_department", "")
        st.session_state.setdefault("v_designation", "")
        st.session_state.setdefault("v_org_address", "")
        st.session_state.setdefault("v_city", "")
        st.session_state.setdefault("v_state", "")
        st.session_state.setdefault("v_postal_code", "")
        st.session_state.setdefault("v_country", "")
        st.session_state.setdefault("v_gender", "")
        st.session_state.setdefault("v_purpose", "")
        st.session_state.setdefault("v_bags", 0)
        st.session_state.setdefault("v_documents", 0)
        st.session_state.setdefault("v_laptop", 0)
        st.session_state.setdefault("v_power_bank", 0)
        st.session_state.setdefault("v_signature_b64", None)
        st.session_state.setdefault("v_photo_b64", None)

    st.markdown("<div class='card wide'>", unsafe_allow_html=True)
    st.subheader("Visitor Registration")

    step = st.session_state["visitor_step"]
    cols = st.columns([1, 1, 1])
    cols[0].markdown(f"**Step 1 — Primary Details**" if step == 1 else "Step 1")
    cols[1].markdown(f"**Step 2 — Secondary Details**" if step == 2 else "Step 2")
    cols[2].markdown(f"**Step 3 — Identity**" if step == 3 else "Step 3")

    st.write("")

    # STEP 1: Primary
    if step == 1:
        st.text_input("Full name", key="v_name")
        st.text_input("Phone", key="v_phone", help="Include country code if required")
        st.text_input("Email", key="v_email")
        st.text_input("Host (person to meet)", key="v_host")
        st.write("")
        col1, col2 = st.columns(2)
        if col1.button("Reset"):
            # clear fields
            st.session_state["v_name"] = ""
            st.session_state["v_phone"] = ""
            st.session_state["v_email"] = ""
            st.session_state["v_host"] = ""
            st.experimental_rerun()
        if col2.button("Next →"):
            # validations
            if not st.session_state["v_name"]:
                st.error("Name required.")
            elif not st.session_state["v_phone"]:
                st.error("Phone required.")
            elif not st.session_state["v_email"] or not is_valid_email(st.session_state["v_email"]):
                st.error("Valid email required.")
            elif not st.session_state["v_host"]:
                st.error("Host is required.")
            else:
                st.session_state["visitor_step"] = 2
                st.experimental_rerun()

    # STEP 2: Secondary
    elif step == 2:
        st.selectbox("Visit Type", ["", "Business", "Personal", "Delivery", "Interview"], key="v_visit_type")
        st.text_input("From Company", key="v_company")
        st.text_input("Department", key="v_department")
        st.text_input("Designation", key="v_designation")
        st.text_area("Organization Address", key="v_org_address")
        col1, col2, col3 = st.columns([2,1,1])
        col1.text_input("City / District", key="v_city")
        col2.text_input("State / Province", key="v_state")
        col3.text_input("Postal Code", key="v_postal_code")
        st.selectbox("Country", ["", "India", "USA", "UK", "Other"], key="v_country")
        st.radio("Gender", ["", "Male", "Female", "Others"], key="v_gender")
        st.selectbox("Purpose", ["", "Meeting", "Delivery", "Interview", "Maintenance", "Other"], key="v_purpose")
        st.multiselect("Belongings (check all that apply)", ["Bags","Documents","Electronic items","Laptop","Charger","Power Bank"], key="v_belongings")
        st.write("")
        col1, col2 = st.columns(2)
        if col1.button("Previous"):
            st.session_state["visitor_step"] = 1
            st.experimental_rerun()
        if col2.button("Next →"):
            # no strict validation here; proceed
            # convert belongings to boolean flags
            belongings = st.session_state.get("v_belongings", [])
            st.session_state["v_bags"] = 1 if "Bags" in belongings else 0
            st.session_state["v_documents"] = 1 if "Documents" in belongings else 0
            st.session_state["v_laptop"] = 1 if "Laptop" in belongings else 0
            st.session_state["v_power_bank"] = 1 if "Power Bank" in belongings else 0
            st.session_state["visitor_step"] = 3
            st.experimental_rerun()

    # STEP 3: Identity
    elif step == 3:
        st.write("Upload a photo (recommended) and signature.")
        photo_file = st.file_uploader("Capture Photo (jpg/png)", type=["png","jpg","jpeg"], key="photo_upload")
        sig_file = st.file_uploader("Upload Signature Image (jpg/png) — OR draw below", type=["png","jpg","jpeg"], key="sig_upload")

        drawn_signature_b64 = None
        if ENABLE_DRAW_SIGNATURE and DRAWABLE_AVAILABLE:
            st.markdown("**Draw signature (optional)**")
            canvas_result = st_canvas(
                stroke_width=2,
                stroke_color="#000",
                background_color="#fff",
                height=200,
                width=600,
                drawing_mode="freedraw",
                key="canvas_sig"
            )
            if canvas_result and canvas_result.image_data is not None:
                # convert numpy array to PIL image then to base64
                img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA').convert("RGB")
                buf = BytesIO()
                img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode()
                drawn_signature_b64 = f"data:image/png;base64,{b64}"

        # Save uploaded files to session state as base64 immediately (so user can go back/forward)
        if photo_file is not None:
            st.session_state["v_photo_b64"] = file_to_base64(photo_file)
        if sig_file is not None:
            st.session_state["v_signature_b64"] = file_to_base64(sig_file)
        if drawn_signature_b64:
            # drawn signature takes precedence over uploaded signature
            st.session_state["v_signature_b64"] = drawn_signature_b64

        st.write("")
        col1, col2 = st.columns(2)
        if col1.button("Previous"):
            st.session_state["visitor_step"] = 2
            st.experimental_rerun()

        if col2.button("Submit Registration"):
            # final validations
            if not st.session_state["v_name"] or not st.session_state["v_phone"] or not st.session_state["v_email"]:
                st.error("Primary details are missing. Please go back and fill them.")
            else:
                # build payload for insert
                payload = {
                    "name": st.session_state["v_name"],
                    "phone": st.session_state["v_phone"],
                    "email": st.session_state["v_email"],
                    "host": st.session_state["v_host"],
                    "time_in": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "checked_in",
                    # secondary (allow NULLs)
                    "company": st.session_state.get("v_company") or None,
                    "visit_type": st.session_state.get("v_visit_type") or None,
                    "department": st.session_state.get("v_department") or None,
                    "designation": st.session_state.get("v_designation") or None,
                    "org_address": st.session_state.get("v_org_address") or None,
                    "city": st.session_state.get("v_city") or None,
                    "state": st.session_state.get("v_state") or None,
                    "postal_code": st.session_state.get("v_postal_code") or None,
                    "country": st.session_state.get("v_country") or None,
                    "gender": st.session_state.get("v_gender") or None,
                    "purpose": st.session_state.get("v_purpose") or None,
                    "bags": int(st.session_state.get("v_bags", 0)),
                    "documents": int(st.session_state.get("v_documents", 0)),
                    "laptop": int(st.session_state.get("v_laptop", 0)),
                    "power_bank": int(st.session_state.get("v_power_bank", 0)),
                    # images
                    "signature_mock": st.session_state.get("v_signature_b64"),
                    "photo_base64": st.session_state.get("v_photo_b64")
                }

                # Insert to DB
                try:
                    inserted_id = insert_visitor(payload)
                    st.success(f"Visitor registered successfully (Log ID: {inserted_id}).")
                    # Reset the form for next entry
                    st.session_state["visitor_step"] = 1
                    # Clear visitor fields (preserve admin session)
                    for k in list(st.session_state.keys()):
                        if k.startswith("v_"):
                            del st.session_state[k]
                    # keep admin auth
                    st.session_state["auth_mode"] = "dashboard"
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed to save visitor: {e}")
    st.markdown("</div>", unsafe_allow_html=True)
