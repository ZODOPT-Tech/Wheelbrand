import streamlit as st
import os
import base64
import mysql.connector
import bcrypt
import boto3
import json
import traceback

# ==============================
# CONFIG
# ==============================
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

LOGO_PATH = "zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


# ==============================
# SECRETS & DB
# ==============================
@st.cache_resource
def get_db_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(resp["SecretString"])


@st.cache_resource
def get_conn():
    c = get_db_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True
    )


# ==============================
# PASSWORD
# ==============================
def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ==============================
# UTIL
# ==============================
def _get_image_base64(path):
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""


def set_auth_view(view):
    st.session_state['conf_auth_view'] = view
    st.rerun()


# ==============================
# CSS
# ==============================
def inject_css():
    st.markdown(f"""
    <style>

    /* Full-width layout (no page_config) */
    .block-container {{
        padding:0 !important;
        max-width:100% !important;
    }}

    body {{
        background:#F8F9FF;
        font-family:'Inter',sans-serif;
    }}

    /* Hide Streamlit UI elements */
    [data-testid="stToolbar"],
    [data-testid="helpButton"],
    [data-testid="baseMenuButton"],
    [data-testid="stActionButtons"],
    [data-testid="collapsedControl"],
    header[data-testid="stHeader"] {{
        display:none !important;
    }}


    /* HEADER */
    .header-box {{
        background:{HEADER_GRADIENT};
        padding:32px 50px;
        border-radius:0 0 28px 28px;
        box-shadow:0 8px 35px rgba(0,0,0,0.18);
        display:flex;
        justify-content:space-between;
        align-items:center;
        width:100%;
    }}

    .header-title {{
        font-size:32px;
        font-weight:800;
        color:white;
    }}

    .logo {{
        height:60px;
    }}


    /* CARD */
    .login-card {{
        background:white;
        width:420px;
        margin:60px auto;
        padding:40px 36px;
        border-radius:18px;
        box-shadow:0 4px 24px rgba(0,0,0,0.1);
    }}

    .stTextInput > div > div > input {{
        background:#F3F5FA;
        border-radius:10px;
        padding:14px;
        font-size:16px;
    }}


    /* BUTTONS */
    .primary-btn {
        background:{HEADER_GRADIENT} !important;
        border:none !important;
        color:white !important;
        font-weight:700 !important;
        padding:14px !important;
        width:100%;
        border-radius:12px !important;
        font-size:16px !important;
        box-shadow:0 6px 24px rgba(80,48,157,0.4);
    }

    .primary-btn:hover {{
        opacity:0.92;
        transform:translateY(-1px);
    }}

    .footer-btn {{
        background:{HEADER_GRADIENT};
        color:white;
        border:none;
        padding:12px 24px;
        border-radius:12px;
        font-size:15px;
        font-weight:700;
        box-shadow:0 6px 24px rgba(80,48,157,0.4);
        width:48%;
        text-align:center;
    }}

    .footer-section {{
        display:flex;
        justify-content:space-between;
        width:420px;
        margin:10px auto 60px auto;
    }}

    @media(max-width:600px){{
        .login-card {{
            width:90%;
            padding:30px 24px;
        }}

        .footer-section {{
            flex-direction:column;
            gap:14px;
            width:90%;
        }}

        .footer-btn {{
            width:100%;
        }}

        .header-title {{
            font-size:24px;
        }}
    }}

    </style>
    """, unsafe_allow_html=True)


# ==============================
# LOGIN VIEW
# ==============================
def render_login_view():
    conn = get_conn()

    st.markdown("<div class='login-card'>", unsafe_allow_html=True)
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In →", help="", on_click=None)

        if submit:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id,name,password_hash FROM conference_users WHERE email=%s",(email,))
            rec = cur.fetchone()
            if rec and check_password(password, rec["password_hash"]):
                st.session_state['user_id'] = rec["id"]
                st.session_state['current_page'] = 'conference_dashboard'
                st.rerun()
            else:
                st.error("Incorrect Email or Password")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="footer-section">
        <button onclick="window.parent.location.reload()" class="footer-btn" id="new-reg">New Registration</button>
        <button onclick="window.parent.location.reload()" class="footer-btn" id="forgot-pass">Forgot Password?</button>
    </div>
    """, unsafe_allow_html=True)

    if st.button("New Registration", key="reg-btn"):
        set_auth_view("register")

    if st.button("Forgot Password?", key="fp-btn"):
        set_auth_view("forgot_password")


# ==============================
# REGISTER & FP views
# ==============================
def render_register_view():
    st.info("Registration form coming...")
    if st.button("← Back"):
        set_auth_view("login")


def render_forgot_password_view():
    st.info("Password reset coming...")
    if st.button("← Back"):
        set_auth_view("login")


# ==============================
# MAIN RENDER
# ==============================
def render_conference_login_page():
    inject_css()

    if 'conf_auth_view' not in st.session_state:
        st.session_state['conf_auth_view'] = 'login'

    view = st.session_state['conf_auth_view']

    # HEADER
    logo = _get_image_base64(LOGO_PATH)
    logo_html = f'<img src="data:image/png;base64,{logo}" class="logo">' if logo else ""

    titles = {
        "login": "CONFERENCE BOOKING",
        "register": "NEW REGISTRATION",
        "forgot_password": "RESET PASSWORD",
    }

    st.markdown(
        f"""
        <div class="header-box">
            <div class="header-title">{titles[view]}</div>
            <div>{logo_html}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if view == "login":
        render_login_view()
    elif view == "register":
        render_register_view()
    else:
        render_forgot_password_view()
