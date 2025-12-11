import streamlit as st
import base64
import mysql.connector
import bcrypt
import boto3
import json
import random
import string
import traceback
import smtplib
from email.mime.text import MIMEText


# =========================================
#  CONFIGURATION
# =========================================
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

LOGO_PATH = "zodopt.png"
LOGO_PLACEHOLDER_TEXT = "ZODOPT"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


# =========================================
#  SECRETS (SMTP + DB)
# =========================================
@st.cache_resource
def get_credentials():
    """Load all credentials from AWS Secrets Manager"""
    try:
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        creds = json.loads(resp["SecretString"])

        return {
            "DB_HOST": creds["DB_HOST"],
            "DB_USER": creds["DB_USER"],
            "DB_PASSWORD": creds["DB_PASSWORD"],
            "DB_NAME": creds["DB_NAME"],

            # SMTP CREDENTIALS
            "SMTP_HOST": creds["SMTP_HOST"],
            "SMTP_PORT": int(creds["SMTP_PORT"]),
            "SMTP_USER": creds["SMTP_USER"],
            "SMTP_PASSWORD": creds["SMTP_PASSWORD"],
        }
    except Exception as e:
        st.error(f"Failed to load secrets: {e}")
        st.write(traceback.format_exc())
        st.stop()


# =========================================
#  SMTP EMAIL SENDER
# =========================================
def send_email(to_email, subject, body):
    creds = get_credentials()

    try:
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = creds["SMTP_USER"]
        msg["To"] = to_email

        # SSL or STARTTLS
        if creds["SMTP_PORT"] == 465:
            server = smtplib.SMTP_SSL(creds["SMTP_HOST"], creds["SMTP_PORT"])
        else:
            server = smtplib.SMTP(creds["SMTP_HOST"], creds["SMTP_PORT"])
            server.starttls()

        server.login(creds["SMTP_USER"], creds["SMTP_PASSWORD"])
        server.sendmail(creds["SMTP_USER"], to_email, msg.as_string())
        server.quit()
        return True

    except Exception as e:
        st.error(f"Email failed: {e}")
        return False


# =========================================
#  DB CONNECTION
# =========================================
def get_db_connection():
    c = get_credentials()
    try:
        return mysql.connector.connect(
            host=c["DB_HOST"],
            user=c["DB_USER"],
            password=c["DB_PASSWORD"],
            database=c["DB_NAME"],
            autocommit=True,
            charset="utf8mb4",
        )
    except:
        return None


def get_live_conn():
    conn = get_db_connection()
    if conn:
        try:
            conn.ping(reconnect=True, attempts=2, delay=1)
            return conn
        except:
            return get_db_connection()
    return None


# =========================================
#  SECURITY
# =========================================
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()


def check_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
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
            cursor.execute("""
                SELECT id, name, password_hash
                FROM conference_users
                WHERE email=%s AND is_active=TRUE
            """, (email,))
            user = cursor.fetchone()
            cursor.close()

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

    c1, c2 = st.columns(2)
    if c1.button("New Registration", use_container_width=True):
        set_auth_view("register")

    if c2.button("Forgot Password?", use_container_width=True):
        set_auth_view("forgot_password")


# =========================================
#  REGISTER – WITH EMAIL NOTIFICATION
# =========================================
def render_register_view():
    conn = get_live_conn()

    DEPTS = ["SELECT", "SALES", "HR", "FINANCE", "DELIVERY/TECH", "DIGITAL MARKETING", "IT"]

    with st.form("conf_register_form"):
        name = st.text_input("Name")
        email = st.text_input("Email ID").lower()
        company = st.text_input("Company")
        dept = st.selectbox("Department", DEPTS)
        password = st.text_input("Password (8+)", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register Account", type="primary")

        if submit:
            if not all([name, email, company, password, confirm]):
                st.error("Fill all fields.")
                return
            if dept == "SELECT":
                st.error("Select a valid department.")
                return
            if password != confirm:
                st.error("Passwords do not match.")
                return
            if len(password) < 8:
                st.error("Password must be 8+ characters.")
                return

            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM conference_users WHERE email=%s", (email,))
            if cursor.fetchone()[0] > 0:
                st.error("Email already registered.")
                return

            hashed = hash_password(password)

            cursor.execute("""
                INSERT INTO conference_users(name,email,company,department,password_hash)
                VALUES(%s,%s,%s,%s,%s)
            """, (name, email, company, dept, hashed))

            # SEND WELCOME EMAIL
            send_email(
                email,
                "Welcome to ZODOPT",
                f"Hello {name},\n\nYour conference account has been created successfully.\nEmail: {email}\n"
            )

            st.success("Registration Successful! Welcome email sent. Please Login.")
            set_auth_view("login")

    if st.button("← Back to Login", use_container_width=True):
        set_auth_view("login")


# =========================================
#  FORGOT PASSWORD – OTP VIA EMAIL
# =========================================
def render_forgot_password_view():
    conn = get_live_conn()

    if "reset_user_id" not in st.session_state:
        st.session_state.reset_user_id = None
        st.session_state.reset_email = None
        st.session_state.email_found = False
        st.session_state.otp_valid = False

    # ---------------------- SEARCH EMAIL ----------------------
    with st.form("forgot_pass_form"):
        email = st.text_input("Enter registered Email ID", value=st.session_state.get("reset_email", ""))

        if st.form_submit_button("Search Account", type="primary"):
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM conference_users WHERE email=%s", (email,))
            user = cursor.fetchone()
            cursor.close()

            if not user:
                st.error("Email not found.")
                return

            st.session_state.reset_email = email
            st.session_state.reset_user_id = user["id"]
            st.session_state.email_found = True

            # Create OTP
            otp = str(random.randint(100000, 999999))

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conference_forgotpassword (user_id, otp_code)
                VALUES (%s, %s)
            """, (user["id"], otp))
            conn.commit()
            cursor.close()

            # Send OTP email
            send_email(
                email,
                "ZODOPT Password Reset Verification Code",
                f"Your verification code is: {otp}\nThis code is valid for 10 minutes."
            )

            st.success("Verification code sent to your email.")
            st.rerun()

    # ---------------------- VERIFY OTP ----------------------
    if st.session_state.email_found and not st.session_state.otp_valid:
        st.markdown("---")
        st.write(f"Reset password for **{st.session_state.reset_email}**")

        with st.form("otp_verify_form"):
            otp_input = st.text_input("Enter 6-digit verification code")

            if st.form_submit_button("Verify Code", type="primary"):
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT id FROM conference_forgotpassword
                    WHERE user_id=%s
                      AND otp_code=%s
                      AND is_used=FALSE
                      AND created_at >= NOW() - INTERVAL 10 MINUTE
                    ORDER BY id DESC
                    LIMIT 1
                """, (st.session_state.reset_user_id, otp_input))
                match = cursor.fetchone()

                if match:
                    cursor.execute("UPDATE conference_forgotpassword SET is_used=TRUE WHERE id=%s", (match["id"],))
                    conn.commit()
                    cursor.close()

                    st.session_state.otp_valid = True
                    st.success("Verification successful! Set new password.")
                else:
                    st.error("Invalid or expired OTP.")

    # ---------------------- RESET PASSWORD ----------------------
    if st.session_state.otp_valid:
        with st.form("reset_pass_form"):
            new = st.text_input("New Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")

            if st.form_submit_button("Change Password", type="primary"):
                if new != confirm:
                    st.error("Passwords do not match.")
                    return
                if len(new) < 8:
                    st.error("Password must be 8+ characters.")
                    return

                hashed = hash_password(new)

                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE conference_users
                    SET password_hash=%s, updated_at=CURRENT_TIMESTAMP
                    WHERE id=%s
                """, (hashed, st.session_state.reset_user_id))
                conn.commit()
                cursor.close()

                st.session_state.reset_email = None
                st.session_state.reset_user_id = None
                st.session_state.email_found = False
                st.session_state.otp_valid = False

                st.success("Password updated successfully! Please Login.")
                set_auth_view("login")

    if st.button("← Back to Login", use_container_width=True):
        st.session_state.reset_email = None
        st.session_state.reset_user_id = None
        st.session_state.email_found = False
        st.session_state.otp_valid = False
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

    st.markdown(f"""
    <style>
    :root {{
        --header-gradient: {HEADER_GRADIENT};
    }}

    .stApp > header {{visibility: hidden;}}

    .header-box {{
        background: var(--header-gradient);
        padding: 20px 40px;
        margin-bottom: 40px;
        border-radius: 0 0 15px 15px;
        color:white;
        font-weight:800;
        font-size:34px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        width:calc(100% + 4rem);
        margin-left:-2rem;
        margin-right:-2rem;
    }}
    </style>
    """, unsafe_allow_html=True)

    logo_base64 = _get_image_base64(LOGO_PATH)
    logo_html = (
        f'<img src="data:image/png;base64,{logo_base64}" style="height:50px;">'
        if logo_base64 else f'<div>{LOGO_PLACEHOLDER_TEXT}</div>'
    )

    st.markdown(
        f"""
        <div class="header-box">
            <div>{header_title}</div>
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if view == "login":
        render_login_view()
    elif view == "register":
        render_register_view()
    else:
        render_forgot_password_view()


# =========================================
#  START APP
# =========================================
if __name__ == "__main__":
    render_conference_login_page()

