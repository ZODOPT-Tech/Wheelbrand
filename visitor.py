# visitor_app.py -- Full refined Streamlit visitor app
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
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

ENABLE_DRAW_SIGNATURE = True  # allow drawing if the package is installed

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
        if "SecretString" not in resp:
            raise RuntimeError("SecretString missing in AWS secrets response.")
        creds = json.loads(resp["SecretString"])
        required_keys = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        for k in required_keys:
            if k not in creds:
                raise RuntimeError(f"Missing key in secret: {k}")
        return creds
    except Exception as e:
        st.error(f"AWS Secret Error: {e}")
        st.write(traceback.format_exc())
        st.stop()


# ---------------- FAST DB CONNECTION ----------------
@st.cache_resource
def get_fast_connection():
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
        return cur.fetchone() is not None
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
        inserted_id = cur.lastrowid
        return inserted_id
    finally:
        cur.close()


# ---------------- IMAGE / SIGNATURE HELPERS ----------------
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
        return "data:application/octet-stream;base64," + base64.b64encode(data).decode()


def typed_text_to_datauri(text: str, width=600, height=120, fontsize=48) -> str:
    """
    Render typed text to a PNG data-uri (simple signature-like image).
    """
    if not text:
        return None
    img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    try:
        # try to use a truetype font if available
        font = ImageFont.truetype("arial.ttf", fontsize)
    except Exception:
        font = ImageFont.load_default()
    w, h = draw.textsize(text, font=font)
    draw.text(((width - w) / 2, (height - h) / 2), text, fill=(0, 0, 0), font=font)
    buf = BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"


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


# ---------------- UI / TABS / NAV ----------------
TAB_CSS = """
<style>
/* Tab container */
.tab-row {
  display:flex;
  gap:2rem;
  justify-content:center;
  align-items:center;
  margin: 12px 0 18px 0;
}
.tab {
  padding: 12px 28px;
  border-radius: 8px 8px 0 0;
  cursor: pointer;
  font-weight: 600;
  color: #6b7280;
  background: #f3f4f6;
  border-bottom: 3px solid transparent;
}
.tab.active {
  color: #0ea5e9;
  background: white;
  border-bottom: 3px solid linear-gradient(90deg,#1e62ff,#8a2eff);
  box-shadow: 0px 4px 12px rgba(0,0,0,0.06);
}
.top-right-logout {
  position: absolute;
  right: 18px;
  top: 18px;
}
</style>
"""


def render_tabs():
    """Render tabs as three clickable columns that set st.session_state['visitor_step']"""
    st.markdown(TAB_CSS, unsafe_allow_html=True)
    step = st.session_state.get("visitor_step", 1)
    # clickable tabs using HTML buttons bound to Streamlit callbacks
    cols = st.columns([1, 1, 1])
    labels = ["PRIMARY DETAILS", "SECONDARY DETAILS", "IDENTITY"]
    for i, col in enumerate(cols, start=1):
        is_active = (i == step)
        btn_label = labels[i - 1]
        # style inline to mimic active state
        class_attr = "tab active" if is_active else "tab"
        # Use button in column
        if col.button(btn_label):
            # only allow navigation to tab i if previous steps satisfied
            if i == 1:
                st.session_state["visitor_step"] = 1
            elif i == 2:
                # allow only if step 1 has valid basic fields
                if st.session_state.get("v_name") and st.session_state.get("v_phone") and is_valid_email(st.session_state.get("v_email", "")):
                    st.session_state["visitor_step"] = 2
                else:
                    st.warning("Complete Primary Details first.")
            elif i == 3:
                if st.session_state.get("v_host"):
                    st.session_state["visitor_step"] = 3
                else:
                    st.warning("Complete Secondary Details first.")
            st.experimental_rerun()


# ---------------- MAIN ----------------
def visitor_main(navigate_to_home_callback=None):
    # initialize session keys safely
    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "login"
    if "admin_logged" not in st.session_state:
        st.session_state["admin_logged"] = False
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "visitor"  # default

    # top header with logout on right
    st.markdown(
        f"""
        <div style="width:100%;padding:12px 18px;border-radius:10px;
            background: linear-gradient(90deg,#1e62ff,#8a2eff);color:white;
            display:flex;justify-content:space-between;align-items:center;">
            <div style="font-size:20px;font-weight:700;">Visitor Management</div>
            <div style="display:flex;gap:10px;align-items:center;">
                <img src="data:image/png;base64,{logo_b64}" style="height:44px;">
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Logout button top-right (navigates to main.py home)
    if st.session_state.get("admin_logged"):
        if st.button("Logout", key="top_logout"):
            # navigate to main.py home by setting current_page
            st.session_state["current_page"] = "home"
            st.session_state["admin_logged"] = False
            st.experimental_rerun()

    mode = st.session_state.get("auth_mode", "login")
    page_title = {
        "login": "Admin Login",
        "register": "Admin Registration",
        "forgot": "Reset Password",
        "dashboard": "Visitor Registration",
    }.get(mode, "Admin Area")
    st.markdown(f"## {page_title}")

    # page routing
    if mode == "login":
        show_login()
    elif mode == "register":
        show_register()
    elif mode == "forgot":
        show_forgot()
    elif mode == "dashboard":
        # ensure visitor state is initialized
        if "v_name" not in st.session_state:
            init_visitor_state()
        show_visitor_flow()


# ---------------- LOGIN ----------------
def show_login():
    st.subheader("Admin Sign In")
    email = st.text_input("Email", key="login_email")
    pwd = st.text_input("Password", type="password", key="login_pwd")

    if st.button("Sign In →", use_container_width=True):
        if not email or not pwd:
            st.error("Email and password are required.")
            return
        res = verify_admin(email.lower(), pwd)
        if res == "SUCCESS":
            st.session_state["auth_mode"] = "dashboard"
            st.session_state["admin_logged"] = True
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error(res)

    col1, col2 = st.columns(2)
    if col1.button("New Registration"):
        st.session_state["auth_mode"] = "register"
        st.experimental_rerun()
    if col2.button("Forgot Password?"):
        st.session_state["auth_mode"] = "forgot"
        st.experimental_rerun()


# ---------------- ADMIN REGISTRATION (AUTO-LOGIN AFTER REG) ----------------
def show_register():
    st.subheader("Register Admin")
    full = st.text_input("Full Name", key="reg_full")
    email = st.text_input("Email", key="reg_email")
    pwd = st.text_input("Password", type="password", key="reg_pwd")
    confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")

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
                st.success("Admin registered — logging you in...")
                login_check = verify_admin(email.lower(), pwd)
                if login_check == "SUCCESS":
                    st.session_state["auth_mode"] = "dashboard"
                    st.session_state["admin_logged"] = True
                    st.experimental_rerun()
                else:
                    st.error("Unexpected login error after registration.")
            else:
                st.error(result)


# ---------------- FORGOT PASSWORD ----------------
def show_forgot():
    st.subheader("Reset Password")
    email = st.text_input("Registered Email", key="forgot_email")
    newpwd = st.text_input("New Password", type="password", key="forgot_new")
    confirm = st.text_input("Confirm Password", type="password", key="forgot_confirm")

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
                st.experimental_rerun()
            else:
                st.error(res)


# ---------------- VISITOR FORM (3 STEPS) ----------------
def show_visitor_flow():
    # ensure visitor state exists
    if "visitor_step" not in st.session_state:
        init_visitor_state()

    # render tab-like UI
    render_tabs()
    step = st.session_state["visitor_step"]
    st.markdown(f"### Step {step} of 3")

    if step == 1:
        step_primary()
    elif step == 2:
        step_secondary()
    elif step == 3:
        step_identity()


def init_visitor_state():
    st.session_state["visitor_step"] = 1
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
    st.session_state["v_signature_type"] = None  # 'draw', 'typed', 'upload'


# ---------- STEP 1 : PRIMARY DETAILS ----------
def step_primary():
    st.subheader("Primary Details")
    st.text_input("Full Name", key="v_name")
    st.text_input("Phone Number", key="v_phone")
    st.text_input("Email Address", key="v_email")

    col1, col2 = st.columns(2)
    if col1.button("Reset"):
        init_visitor_state()
        st.experimental_rerun()

    if col2.button("Next →"):
        if not st.session_state["v_name"]:
            st.error("Name is required.")
        elif not st.session_state["v_phone"]:
            st.error("Phone number required.")
        elif not is_valid_email(st.session_state["v_email"]):
            st.error("Enter valid email.")
        else:
            st.session_state["visitor_step"] = 2
            st.experimental_rerun()


# ---------- STEP 2 : SECONDARY DETAILS ----------
def step_secondary():
    st.subheader("Secondary Details (Person to Visit & Visit Info)")
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
        st.experimental_rerun()

    if col2.button("Next →"):
        if not st.session_state["v_host"]:
            st.error("Person to Visit is required.")
        else:
            st.session_state["visitor_step"] = 3
            st.experimental_rerun()


# ---------- STEP 3 : IDENTITY ----------
def step_identity():
    st.subheader("Identity Verification")
    st.write("Upload Photo and provide a signature (Draw / Type / Upload)")

    # photo
    photo = st.file_uploader("Photo", type=["png", "jpg", "jpeg"], key="photo_uploader")
    if photo:
        st.session_state["v_photo_b64"] = file_to_base64(photo)

    # Signature options
    st.write("Signature method:")
    sig_method = st.selectbox("Choose signature type", ["", "Draw", "Type", "Upload"], key="sig_method")

    # Draw option
    if sig_method == "Draw":
        st.session_state["v_signature_type"] = "draw"
        if DRAWABLE_AVAILABLE and ENABLE_DRAW_SIGNATURE:
            canvas = st_canvas(
                stroke_width=2,
                stroke_color="#000000",
                background_color="#ffffff",
                height=200,
                width=600,
                drawing_mode="freedraw",
                key="canvas_sig"
            )
            if canvas and canvas.image_data is not None:
                # convert to PNG data-uri
                img = Image.fromarray(canvas.image_data.astype("uint8"), "RGBA").convert("RGB")
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state["v_signature_b64"] = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
        else:
            st.info("Drawable canvas not available on this environment. Use Type or Upload.")

    # Type option
    elif sig_method == "Type":
        st.session_state["v_signature_type"] = "typed"
        typed = st.text_input("Type your signature (name)", key="typed_sig")
        if typed:
            st.session_state["v_signature_b64"] = typed_text_to_datauri(typed)

    # Upload option
    elif sig_method == "Upload":
        st.session_state["v_signature_type"] = "upload"
        sig_file = st.file_uploader("Upload Signature image", type=["png", "jpg", "jpeg"], key="sig_uploader")
        if sig_file:
            st.session_state["v_signature_b64"] = file_to_base64(sig_file)

    # preview (if any)
    if st.session_state.get("v_signature_b64"):
        st.markdown("**Signature Preview:**")
        st.image(st.session_state["v_signature_b64"], width=300)

    col1, col2 = st.columns(2)
    if col1.button("← Back"):
        st.session_state["visitor_step"] = 2
        st.experimental_rerun()

    if col2.button("Submit Registration"):
        # basic validation
        if not st.session_state.get("v_photo_b64"):
            st.error("Photo is required.")
            return
        if not st.session_state.get("v_signature_b64"):
            st.error("Signature required (choose Draw / Type / Upload).")
            return

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
            # move to completed view
            show_completed(visitor_id)
        except Exception as e:
            st.error(f"Error saving visitor: {e}")
            st.write(traceback.format_exc())


# ---------- COMPLETED ----------
def show_completed(visitor_id):
    st.success(f"Registration done! (Log ID: {visitor_id})")
    st.write("What would you like to do next?")

    c1, c2 = st.columns(2)
    if c1.button("New Registration"):
        init_visitor_state()
        st.experimental_rerun()

    if c2.button("Back to Login"):
        # set to login screen inside visitor.py
        st.session_state["auth_mode"] = "login"
        st.session_state["admin_logged"] = False
        st.experimental_rerun()


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    # consistent initialization
    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "login"
    if "admin_logged" not in st.session_state:
        st.session_state["admin_logged"] = False
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "visitor"

    visitor_main()
