import streamlit as st
import base64
import mysql.connector
import bcrypt
import boto3
import json
import traceback


# =========================================
#  CONFIGURATION
# =========================================
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

LOGO_PATH = "zodopt.png"
LOGO_PLACEHOLDER_TEXT = "ZODOPT"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


# =========================================
#  SECRETS (CACHED SAFE)
# =========================================
@st.cache_resource
def get_db_credentials():
    try:
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        creds = json.loads(resp["SecretString"])
        return {
            "DB_HOST": creds["DB_HOST"],
            "DB_USER": creds["DB_USER"],
            "DB_PASSWORD": creds["DB_PASSWORD"],
            "DB_NAME": creds["DB_NAME"],
        }
    except Exception as e:
        st.error(f"Failed to load AWS secrets: {e}")
        st.write(traceback.format_exc())
        st.stop()


# =========================================
#  DB CONNECTION (NO CACHE)
# =========================================
def get_db_connection():
    c = get_db_credentials()
    try:
        conn = mysql.connector.connect(
            host=c["DB_HOST"],
            user=c["DB_USER"],
            password=c["DB_PASSWORD"],
            database=c["DB_NAME"],
            autocommit=True,
            charset="utf8mb4",
            connection_timeout=8,
        )
        return conn
    except:
        return None


def get_live_conn():
    """
    Guarantee live MySQL session.
    """
    conn = get_db_connection()
    if conn:
        try:
            conn.ping(reconnect=True, attempts=2, delay=1)
            return conn
        except:
            return get_db_connection()
    return None


# =========================================
#  SECURITY HELPERS
# =========================================
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")


def check_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except:
        return False


# =========================================
#  UTILITIES
# =========================================
def _get_image_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""


def set_auth_view(view):
    st.session_state["conf_auth_view"] = view
    st.rerun()


# =========================================
#  LOGIN VIEW
# =========================================
def render_login_view():
    conn = get_live_conn()

    with st.form("conf_login_form"):
        email = st.text_input("Email ID")
        password = st.text_input("Password", type="password")

        submit = st.form_submit_button("Sign In →", type="primary")

        if submit:
            if not email or not password:
                st.error("Enter both email and password.")
                return

            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT id, name, password_hash 
                    FROM conference_users
                    WHERE email=%s AND is_active=TRUE
                    """,
                    (email,),
                )
                user = cursor.fetchone()

                if user and check_password(password, user["password_hash"]):
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user["id"]
                    st.session_state["user_email"] = email
                    st.session_state["user_name"] = user["name"]
                    st.session_state["current_page"] = "conference_dashboard"
                    st.success(f"Welcome {user['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid Email or Password.")

            except mysql.connector.Error as err:
                st.error(f"Database error: {err}")
            finally:
                cursor.close()

    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("New Registration", use_container_width=True):
            set_auth_view("register")
    with c2:
        if st.button("Forgot Password?", use_container_width=True):
            set_auth_view("forgot_password")


# =========================================
#  REGISTER VIEW
# =========================================
def render_register_view():
    conn = get_live_conn()

    DEPTS = ["SELECT", "SALES", "HR", "FINANCE", "DELIVERY/TECH", "DIGITAL MARKETING", "IT"]

    with st.form("conf_register_form"):
        name = st.text_input("Name")
        email = st.text_input("Email ID")
        company = st.text_input("Company")
        dept = st.selectbox("Department", DEPTS)
        password = st.text_input("Password (8+)", type="password")
        confirm = st.text_input("Confirm Password", type="password")

        submit = st.form_submit_button("Register Account", type="primary")

        if submit:
            if not all([name, email, company, password, confirm]):
                st.error("Fill all fields.")
            elif dept == "SELECT":
                st.error("Select a valid department.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif len(password) < 8:
                st.error("Password must be 8+ characters.")
            else:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "SELECT COUNT(*) FROM conference_users WHERE email=%s",
                        (email,),
                    )
                    if cursor.fetchone()[0] > 0:
                        st.error("Email already registered.")
                        return

                    hashed = hash_password(password)
                    cursor.execute(
                        """
                        INSERT INTO conference_users(name,email,company,department,password_hash)
                        VALUES(%s,%s,%s,%s,%s)
                        """,
                        (name, email, company, dept, hashed),
                    )

                    st.success("Registration Successful! Please Login.")
                    set_auth_view("login")

                except mysql.connector.Error as err:
                    st.error(f"DB error: {err}")
                finally:
                    cursor.close()

    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    if st.button("← Back to Login", use_container_width=True):
        set_auth_view("login")


# =========================================
#  FORGOT PASSWORD VIEW
# =========================================
def render_forgot_password_view():
    conn = get_live_conn()

    if "reset_email" not in st.session_state:
        st.session_state.reset_email = None
        st.session_state.email_found = False

    with st.form("forgot_pass_form"):
        email = st.text_input("Enter registered Email ID", value=st.session_state.get("reset_email", ""))

        if st.form_submit_button("Search Account", type="primary"):
            if not email:
                st.warning("Enter email.")
                return

            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT id FROM conference_users WHERE email=%s",
                    (email,),
                )
                found = cursor.fetchone()

                if found:
                    st.session_state.reset_email = email
                    st.session_state.email_found = True
                    st.success("Account found. Enter new password.")
                    st.rerun()
                else:
                    st.error("Email not found.")
            except mysql.connector.Error as err:
                st.error(f"DB error: {err}")
            finally:
                cursor.close()

    if st.session_state.email_found:
        st.markdown("---")
        st.write(f"Reset password for: `{st.session_state.reset_email}`")

        with st.form("reset_pass_form"):
            new = st.text_input("New Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")

            if st.form_submit_button("Change Password", type="primary"):
                if new != confirm:
                    st.error("Passwords do not match.")
                elif len(new) < 8:
                    st.error("Password must be 8+ characters.")
                else:
                    cursor = conn.cursor()
                    try:
                        hashed = hash_password(new)
                        cursor.execute(
                            """
                            UPDATE conference_users
                            SET password_hash=%s, updated_at=CURRENT_TIMESTAMP
                            WHERE email=%s
                            """,
                            (hashed, st.session_state.reset_email),
                        )
                        st.success("Password updated. Login now.")
                        st.session_state.reset_email = None
                        st.session_state.email_found = False
                        set_auth_view("login")
                    except mysql.connector.Error as err:
                        st.error(f"DB error: {err}")
                    finally:
                        cursor.close()

    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    if st.button("← Back to Login", use_container_width=True):
        st.session_state.reset_email = None
        st.session_state.email_found = False
        set_auth_view("login")


# =========================================
#  MAIN ROUTER + HEADER UI
# =========================================
def render_conference_login_page():
    if "conf_auth_view" not in st.session_state:
        st.session_state.conf_auth_view = "login"

    view = st.session_state.conf_auth_view

    if view == "login":
        header_title = "CONFERENCE BOOKING - SIGN IN"
    elif view == "register":
        header_title = "NEW REGISTRATION"
    else:
        header_title = "RESET PASSWORD"

    # --- HEADER STYLE ---
    st.markdown(f"""
    <style>
    :root {{
        --header-gradient: {HEADER_GRADIENT};
        --primary: #50309D;
        --secondary: #7A42FF;
    }}

    html, body, .stApp .main {{
        padding-top: 0px !important;
        margin-top: 0px !important;
    }}
    .stApp > header {{
        visibility: hidden;
    }}

    .header-box {{
        background: var(--header-gradient);
        padding: 20px 40px;
        margin-bottom: 40px;
        border-radius: 0 0 15px 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.25);
        display:flex;
        justify-content:space-between;
        align-items:center;
        width:calc(100% + 4rem);
        margin-left:-2rem;
        margin-right:-2rem;
    }}
    .header-title {{
        font-family:Inter;
        font-size:34px;
        font-weight:800;
        color:#FFF;
        margin:0;
    }}
    .header-logo-container {{
        font-size:20px;
        font-weight:600;
        color:#FFF;
    }}
    </style>
    """, unsafe_allow_html=True)

    logo_base64 = _get_image_base64(LOGO_PATH)
    logo_html = (f'<img src="data:image/png;base64,{logo_base64}" style="height:50px;">'
                 if logo_base64 else f'<div class="header-logo-container">{LOGO_PLACEHOLDER_TEXT}</div>')

    st.markdown(
        f"""
        <div class="header-box">
            <div class="header-title">{header_title}</div>
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # VIEW ROUTING
    if view == "login":
        render_login_view()
    elif view == "register":
        render_register_view()
    else:
        render_forgot_password_view()
