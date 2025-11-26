# visitor_app.py -- Refined full Streamlit app using AWS Secrets Manager for DB credentials
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
import traceback

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

ENABLE_DRAW_SIGNATURE = False # Set True if you want the drawable signature option

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
    """
    Loads DB credentials from AWS Secrets Manager.
    Secret must be a JSON string with keys:
    DB_HOST, DB_NAME, DB_USER, DB_PASSWORD
    """
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    try:
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        # SecretsManager stores text in 'SecretString'
        if "SecretString" not in resp:
            raise RuntimeError("SecretString missing in AWS secrets response.")
        creds = json.loads(resp["SecretString"])
        required_keys = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        for k in required_keys:
            if k not in creds:
                raise RuntimeError(f"Missing key in secret: {k}")
        return creds
    except Exception as e:
        # helpful error visible in Streamlit
        st.error(f"AWS Secret Error: {e}")
        # show traceback in logs for debugging (not necessary for end users)
        st.write(traceback.format_exc())
        st.stop()


# ---------------- FAST DB CONNECTION ----------------
@st.cache_resource
def get_fast_connection():
    """
    Returns a persistent connection object (cached by Streamlit)
    Note: do not close this connection (Streamlit caches it).
    Close cursors after use.
    """
    c = get_db_credentials()
    try:
        conn = mysql.connector.connect(
            host=c["DB_HOST"],
            user=c["DB_USER"],
            password=c["DB_PASSWORD"],
            database=c["DB_NAME"],
            port=3306,
            autocommit=True,
            connection_timeout=10,
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"DB Connection Error: {e}")
        st.stop()


# ---------------- DB FUNCTIONS ----------------
def email_exists(email: str) -> bool:
    conn = get_fast_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT 1 FROM {DB_TABLE} WHERE email=%s LIMIT 1", (email,))
        exists = cur.fetchone() is not None
        return exists
    finally:
        cur.close()


def create_admin(full: str, email: str, pwd: str) -> str:
    if email_exists(email):
        return "Email already exists."

    hashed = make_bcrypt_hash(pwd)
    conn = get_fast_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            f"INSERT INTO {DB_TABLE}(full_name, email, password_hash, created_at) VALUES (%s, %s, %s, %s)",
            (full, email, hashed, datetime.utcnow()),
        )
        return "SUCCESS"
    except mysql.connector.Error as e:
        return f"DB Error creating admin: {e}"
    finally:
        cur.close()


def verify_admin(email: str, pwd: str) -> str:
    conn = get_fast_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT password_hash FROM {DB_TABLE} WHERE email=%s LIMIT 1", (email,))
        row = cur.fetchone()
        if not row:
            return "Email not found."
        return "SUCCESS" if check_bcrypt(pwd, row[0]) else "Incorrect password."
    finally:
        cur.close()


def update_password(email: str, newpwd: str) -> str:
    hashed = make_bcrypt_hash(newpwd)
    conn = get_fast_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"UPDATE {DB_TABLE} SET password_hash=%s WHERE email=%s", (hashed, email))
        return "SUCCESS"
    except mysql.connector.Error as e:
        return f"DB Error updating password: {e}"
    finally:
        cur.close()


# ---------------- VISITOR INSERT ----------------
def insert_visitor(payload: dict):
    conn = get_fast_connection()
    cur = conn.cursor()
    try:
        cols = ",".join(payload.keys())
        placeholders = ",".join(["%s"] * len(payload))
        sql = f"INSERT INTO {VISITOR_TABLE} ({cols}) VALUES ({placeholders})"
        cur.execute(sql, tuple(payload.values()))
        # lastrowid works with mysql-connector
        inserted_id = cur.lastrowid
        return inserted_id
    finally:
        cur.close()


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
    except Exception:
        # fallback for non-image files
        return "data:application/octet-stream;base64," + base64.b64encode(data).decode()


# ---------------- LOGO ----------------
def load_logo(path):
    try:
        img = Image.open(path)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


logo_b64 = load_logo(LOGO_PATH)


# ---------------- UI / MAIN ----------------
def logout():
    """Clear session state and navigate to login."""
    for key in ["auth_mode", "admin_logged", "visitor_step"]:
        if key in st.session_state:
            del st.session_state[key]
    init_visitor_state() # Reset visitor state as well
    st.session_state["auth_mode"] = "login"
    st.rerun()

def visitor_main(navigate_to=None):
    # header styling
    st.markdown(
        """
        <style>
            /* Custom styling for the primary action button */
            .stButton button {
                background-color: #1e62ff !important;
                color: white !important;
                border: 1px solid #1e62ff !important;
                border-radius: 0.5rem !important;
                transition: all 0.3s ease;
            }
            .stButton button:hover {
                background-color: #8a2eff !important;
                border-color: #8a2eff !important;
                color: white !important;
                box-shadow: 0 4px 12px rgba(138, 46, 255, 0.4);
            }
            /* Custom styling for the tab-like headers in visitor flow */
            div.visitor-tab-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #ddd;
                margin-bottom: 20px;
            }
            div.visitor-tab {
                flex-grow: 1;
                text-align: center;
                padding: 15px 10px;
                cursor: pointer;
                font-weight: 600;
                color: #888;
                position: relative;
            }
            div.visitor-tab.active {
                color: #1e62ff; /* Primary color for active tab text */
            }
            div.visitor-tab.active::after {
                content: '';
                position: absolute;
                bottom: -1px;
                left: 0;
                right: 0;
                height: 4px;
                /* Gradient line matching the image */
                background: linear-gradient(90deg, #1e62ff, #8a2eff);
                border-radius: 2px 2px 0 0;
            }
            /* Styling for the logout button in the header */
            .logout-container {
                display: flex;
                align-items: center;
                margin-left: 20px; /* Spacing from the logo/title */
            }
            .logout-button {
                background: none !important;
                border: none !important;
                padding: 0 !important;
                margin: 0 !important;
                box-shadow: none !important;
            }
            .logout-button i {
                font-size: 24px; /* Icon size */
                color: white; /* Icon color */
                cursor: pointer;
            }
            /* Ensure font awesome is available or use another icon set. Streamlit uses its own icons which can be used via markdown/html */
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        """,
        unsafe_allow_html=True,
    )

    mode = st.session_state.get("auth_mode", "login")
    page_title = {
        "login": "Admin Login",
        "register": "Admin Registration",
        "forgot": "Reset Password",
        "dashboard": "Visitor Registration",
    }.get(mode, "Admin Area")

    # Header with Logo and Title
    header_html = f"""
    <div style="width:100%;padding:20px 30px;border-radius:15px;
        background: linear-gradient(90deg,#1e62ff,#8a2eff);color:white;
        display:flex;justify-content:space-between;align-items:center;">
        <div style="font-size:28px;font-weight:700;">{page_title}</div>
        <div style="display:flex;align-items:center;">
            <img src="data:image/png;base64,{logo_b64}" style="height:60px;margin-right:20px;">
    """
    
    # Add Logout Button only on the 'dashboard' page
    if mode == "dashboard":
        # The button itself will be rendered outside the markdown block for Streamlit functionality
        header_html += """
            <div class="logout-container">
                <form action="." method="GET">
                    <button type="submit" name="logout" class="logout-button" style="background:none; border:none; padding:0; margin:0; box-shadow:none;">
                        <i class="fas fa-sign-out-alt"></i>
                    </button>
                </form>
            </div>
        """
    
    header_html += "</div></div>"
    st.markdown(header_html, unsafe_allow_html=True)

    # Check for logout query parameter (from the button form submission)
    if "logout" in st.query_params:
        logout()
    
    # Main content rendering based on mode
    if mode == "login":
        show_login()
    elif mode == "register":
        show_register()
    elif mode == "forgot":
        show_forgot()
    elif mode == "dashboard":
        show_visitor_flow()


# ---------------- LOGIN ----------------
def show_login():
    st.subheader("Admin Sign In")
    email = st.text_input("Email")
    pwd = st.text_input("Password", type="password")

    if st.button("Sign In →", use_container_width=True):
        if not email or not pwd:
            st.error("Email and password are required.")
            return
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
def show_register():
    st.subheader("Register Admin")
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
def show_forgot():
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
            res = update_password(email.lower(), newpwd)
            if res == "SUCCESS":
                st.success("Password updated!")
                st.session_state["auth_mode"] = "login"
                st.rerun()
            else:
                st.error(res)


# ---------------- VISITOR FORM (3 STEPS) ----------------
def show_visitor_flow():
    if "visitor_step" not in st.session_state:
        init_visitor_state()

    step = st.session_state["visitor_step"]
    
    # Custom tab rendering logic
    tab_titles = {1: "PRIMARY DETAILS", 2: "SECONDARY DETAILS", 3: "IDENTITY"}
    
    # Use HTML/CSS to mimic the tab structure from the image
    tab_html = '<div class="visitor-tab-header">'
    for i in range(1, 4):
        active_class = "active" if i == step else ""
        # Using a button as a trick to capture click, or just rely on the existing multi-step logic
        # For simplicity and to not overcomplicate the re-rendering logic with st.button, we'll just render the titles
        tab_html += f'<div class="visitor-tab {active_class}">{tab_titles[i]}</div>'
    tab_html += '</div>'
    
    st.markdown(tab_html, unsafe_allow_html=True)
    
    # Render the content for the current step
    if step == 1:
        step_primary()
    elif step == 2:
        step_secondary()
    elif step == 3:
        step_identity()


def init_visitor_state():
    st.session_state["visitor_step"] = 1
    # Primary + Secondary + Identity fields
    fields = [
        "v_name", "v_phone", "v_email",
        "v_host", "v_company", "v_visit_type", "v_department", "v_designation",
        "v_org_address", "v_city", "v_state", "v_postal_code", "v_country",
        "v_gender", "v_purpose"
    ]
    for f in fields:
        st.session_state[f] = ""

    st.session_state["v_bags"] = 0
    st.session_state["v_documents"] = 0
    st.session_state["v_laptop"] = 0
    st.session_state["v_power_bank"] = 0
    st.session_state["v_signature_b64"] = None
    st.session_state["v_photo_b64"] = None


# ---------- STEP 1 : PRIMARY DETAILS ----------
def step_primary():
    # st.subheader("Primary Details") # Removed subheader to fit the tab look better
    st.text_input("Full Name", key="v_name")
    st.text_input("Phone Number", key="v_phone")
    st.text_input("Email Address", key="v_email")

    col1, col2 = st.columns(2)
    if col1.button("Reset"):
        init_visitor_state()
        st.rerun()

    if col2.button("Next →"):
        if not st.session_state["v_name"]:
            st.error("Name is required.")
        elif not st.session_state["v_phone"]:
            st.error("Phone number required.")
        elif not is_valid_email(st.session_state["v_email"]):
            st.error("Enter valid email.")
        else:
            # unlock secondary
            st.session_state["visitor_step"] = 2
            st.rerun()


# ---------- STEP 2 : SECONDARY DETAILS ----------
def step_secondary():
    # st.subheader("Secondary Details (Person to Visit & Visit Info)") # Removed subheader
    st.text_input("Person to Visit", key="v_host")
    st.selectbox("Visit Type", ["", "Business", "Personal", "Delivery", "Interview"], key="v_visit_type")
    st.text_input("From Company", key="v_company")
    st.text_input("Department", key="v_department")
    st.text_input("Designation", key="v_designation")
    st.text_area("Organization Address", key="v_org_address")

    c1, c2, c3 = st.columns([2, 1, 1])
    c1.text_input("City", key="v_city")
    c2.text_input("State", key="v_state")
    c3.text_input("Postal Code", key="v_postal_code")

    st.selectbox("Country", ["", "India", "USA", "UK", "Other"], key="v_country")
    st.radio("Gender", ["", "Male", "Female", "Others"], key="v_gender")
    st.selectbox("Purpose of Visit", ["", "Meeting", "Delivery", "Interview", "Maintenance", "Other"], key="v_purpose")

    belongings = st.multiselect("Belongings", ["Bags", "Documents", "Laptop", "Power Bank"])
    st.session_state["v_bags"] = 1 if "Bags" in belongings else 0
    st.session_state["v_documents"] = 1 if "Documents" in belongings else 0
    st.session_state["v_laptop"] = 1 if "Laptop" in belongings else 0
    st.session_state["v_power_bank"] = 1 if "Power Bank" in belongings else 0

    col1, col2 = st.columns(2)
    if col1.button("← Back"):
        st.session_state["visitor_step"] = 1
        st.rerun()

    if col2.button("Next →"):
        if not st.session_state["v_host"]:
            st.error("Person to Visit is required.")
        else:
            st.session_state["visitor_step"] = 3
            st.rerun()


# ---------- STEP 3 : IDENTITY ----------
def step_identity():
    # st.subheader("Identity Verification") # Removed subheader
    st.write("Upload Photo and Signature")

    photo = st.file_uploader("Photo", type=["png", "jpg", "jpeg"])
    signature = st.file_uploader("Signature", type=["png", "jpg", "jpeg"])

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
            key="canvas_sig",
        )
        if canvas.image_data is not None:
            img = Image.fromarray(canvas.image_data.astype("uint8"), "RGBA").convert("RGB")
            buf = BytesIO()
            img.save(buf, format="PNG")
            encoded = base64.b64encode(buf.getvalue()).decode()
            st.session_state["v_signature_b64"] = f"data:image/png;base64,{encoded}"

    col1, col2 = st.columns(2)
    if col1.button("← Back"):
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
            "photo_base64": st.session_state["v_photo_b64"],
        }

        try:
            visitor_id = insert_visitor(payload)
            st.success(f"Visitor Registered Successfully (Log ID: {visitor_id})")
            init_visitor_state()
            st.rerun()
        except Exception as e:
            st.error(f"Error saving visitor: {e}")
            st.write(traceback.format_exc())


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    # top-level navigation (kept minimal)
    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "login"
    visitor_main()
