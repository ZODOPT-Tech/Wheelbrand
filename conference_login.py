import streamlit as st
import os
import base64
import mysql.connector
import bcrypt
import boto3
import json
import traceback


# ----------------------------------------------
# AWS CONFIG
# ----------------------------------------------
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"


# ----------------------------------------------
# SECURE SECRETS LOADER (CACHE SAFE)
# ----------------------------------------------
@st.cache_resource
def get_db_credentials():
    """
    Load DB credentials from AWS Secrets Manager.
    Stores only credentials in cache, not connection.
    """
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    try:
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)

        if "SecretString" not in resp:
            raise RuntimeError("SecretString missing in secrets response.")

        creds = json.loads(resp["SecretString"])

        required = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        for key in required:
            if key not in creds:
                raise RuntimeError(f"Missing key in secret: {key}")

        return creds

    except Exception as e:
        st.error(f"Cannot load DB credentials: {e}")
        st.write(traceback.format_exc())
        st.stop()


# ----------------------------------------------
# SAFE CONNECTION (NO CACHE)
# ----------------------------------------------
def get_db_connection():
    """
    ALWAYS return a fresh MySQL connection.
    DO NOT CACHE CONNECTION.
    """
    creds = get_db_credentials()
    try:
        conn = mysql.connector.connect(
            host=creds["DB_HOST"],
            user=creds["DB_USER"],
            password=creds["DB_PASSWORD"],
            database=creds["DB_NAME"],
            port=3306,
            autocommit=True,
            connection_timeout=10,
        )
        return conn

    except mysql.connector.Error as e:
        st.error(f"MySQL Connection not available: {e}")
        return None


# ----------------------------------------------
# GUARANTEED LIVE CONNECTION
# ----------------------------------------------
def get_live_conn():
    """
    Ensures connection is alive. Reconnects if dead.
    """
    conn = get_db_connection()
    if conn:
        try:
            conn.ping(reconnect=True, attempts=3, delay=2)
            return conn
        except:
            return get_db_connection()
    return None


# ----------------------------------------------
# SECURITY
# ----------------------------------------------
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")


def check_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except:
        return False


# ----------------------------------------------
# UTILS
# ----------------------------------------------
def _get_image_base64(path):
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""


def set_auth_view(view):
    st.session_state["conf_auth_view"] = view
    st.rerun()


# ----------------------------------------------
# LOGIN VIEW
# ----------------------------------------------
def render_login_view():
    conn = get_live_conn()

    with st.form("conf_login_form"):
        email = st.text_input("Email ID", key="conf_login_email")
        password = st.text_input("Password", type="password", key="conf_login_password")

        submitted = st.form_submit_button("Sign In →", type="primary")

        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
                return

            cursor = conn.cursor(dictionary=True)

            try:
                query = """
                SELECT id, name, password_hash
                FROM conference_users
                WHERE email = %s AND is_active = TRUE
                """
                cursor.execute(query, (email,))
                user = cursor.fetchone()

                if user and check_password(password, user["password_hash"]):
                    st.success(f"Welcome, {user['name']}")

                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user["id"]
                    st.session_state["user_email"] = email
                    st.session_state["user_name"] = user["name"]
                    st.session_state["current_page"] = "conference_dashboard"
                    st.rerun()

                else:
                    st.error("Invalid Email ID or Password.")

            except mysql.connector.Error as err:
                st.error(f"Database error: {err}")
            finally:
                cursor.close()

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Registration", use_container_width=True):
            set_auth_view("register")
    with col2:
        if st.button("Forgot Password?", use_container_width=True):
            set_auth_view("forgot_password")


# ----------------------------------------------
# REGISTER VIEW
# ----------------------------------------------
def render_register_view():
    conn = get_live_conn()

    DEPT = ["SELECT", "SALES", "HR", "FINANCE", "DELIVERY/TECH", "DIGITAL MARKETING", "IT"]

    with st.form("conf_register_form"):
        name = st.text_input("Name")
        email = st.text_input("Email ID")
        company = st.text_input("Company")
        department = st.selectbox("Department", DEPT)
        password = st.text_input("Password (8+)", type="password")
        confirm = st.text_input("Confirm Password", type="password")

        submitted = st.form_submit_button("Register Account", type="primary")

        if submitted:
            if not all([name, email, company, password, confirm]):
                st.error("Fill all fields.")
            elif department == "SELECT":
                st.error("Select a department.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters.")
            else:
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT COUNT(*) FROM conference_users WHERE email = %s", (email,))
                    if cursor.fetchone()[0] > 0:
                        st.error("Email already registered.")
                        return

                    hashed = hash_password(password)
                    cursor.execute(
                        """
                        INSERT INTO conference_users (name, email, company, department, password_hash)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (name, email, company, department, hashed)
                    )

                    st.success("Registration successful!")
                    set_auth_view("login")

                except mysql.connector.Error as err:
                    st.error(f"Database error: {err}")
                finally:
                    cursor.close()

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    if st.button("← Back to Login", use_container_width=True):
        set_auth_view("login")


# ----------------------------------------------
# FORGOT PASSWORD VIEW
# ----------------------------------------------
def render_forgot_password_view():
    conn = get_live_conn()

    if "reset_email" not in st.session_state:
        st.session_state.reset_email = None
        st.session_state.email_found = False

    with st.form("forgot_email"):
        email = st.text_input("Enter registered Email ID", value=st.session_state.get("reset_email", ""))

        if st.form_submit_button("Search Account", type="primary"):
            if not email:
                st.warning("Enter email.")
                return

            cursor = conn.cursor()
            try:
                cursor.execute("SELECT id FROM conference_users WHERE email = %s", (email,))
                found = cursor.fetchone()

                if found:
                    st.session_state.reset_email = email
                    st.session_state.email_found = True
                    st.success("Account found. Enter new password below.")
                    st.rerun()
                else:
                    st.error("Email not found.")

            except mysql.connector.Error as err:
                st.error(f"Database error: {err}")
            finally:
                cursor.close()

    if st.session_state.email_found:
        st.markdown("---")
        st.write(f"Reset password for: `{st.session_state.reset_email}`")

        with st.form("reset_pass"):
            new = st.text_input("New Password (8+)", type="password")
            confirm = st.text_input("Confirm New Password", type="password")

            if st.form_submit_button("Change Password", type="primary"):
                if new != confirm:
                    st.error("Passwords do not match.")
                elif len(new) < 8:
                    st.error("Password must be 8+ chars.")
                else:
                    cursor = conn.cursor()
                    try:
                        hashed = hash_password(new)
                        cursor.execute(
                            """
                            UPDATE conference_users
                            SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE email = %s
                            """,
                            (hashed, st.session_state.reset_email)
                        )
                        st.success("Password updated. Login now.")
                        st.session_state.email_found = False
                        st.session_state.reset_email = None
                        set_auth_view("login")

                    except mysql.connector.Error as err:
                        st.error(f"Database error: {err}")
                    finally:
                        cursor.close()

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    if st.button("← Back to Login", use_container_width=True):
        st.session_state.email_found = False
        st.session_state.reset_email = None
        set_auth_view("login")


# ----------------------------------------------
# MAIN ROUTER
# ----------------------------------------------
def render_conference_login_page():
    if "conf_auth_view" not in st.session_state:
        st.session_state.conf_auth_view = "login"

    view = st.session_state.conf_auth_view

    if view == "login":
        render_login_view()
    elif view == "register":
        render_register_view()
    elif view == "forgot_password":
        render_forgot_password_view()
