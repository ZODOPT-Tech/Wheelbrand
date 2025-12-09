import streamlit as st
import os
import base64
import mysql.connector
import bcrypt
import boto3
import json
import traceback

AWS_REGION = "ap-south-1" 
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS" 

LOGO_PATH = "zodopt.png" 
LOGO_PLACEHOLDER_TEXT = "zodopt"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


# ================= AWS SECRETS =================
@st.cache_resource
def get_db_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(resp["SecretString"])


@st.cache_resource
def get_fast_connection():
    c = get_db_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True,
    )


# ================= PASSWORD =================
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()


def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


# ================= UTIL =================
def _get_image_base64(path):
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""


def set_auth_view(view):
    st.session_state['conf_auth_view'] = view
    st.rerun()


# ================= CUSTOM CSS =================
def inject_css():
    st.markdown(f"""
    <style>

    /* ===== FULL WIDTH PAGE ===== */
    .block-container {{
        padding: 0 !important;
        margin: 0 auto !important;
        max-width: 100% !important;
    }}

    /* Remove toolbar buttons */
    [data-testid="stToolbar"] {{
        display: none !important;
    }}

    /* Remove hamburger menu */
    [data-testid="baseMenuButton"] {{
        display: none !important;
    }}

    /* Remove help button */
    [data-testid="helpButton"] {{
        display:none !important;
    }}

    /* Remove floating debug controls */
    [data-testid="collapsedControl"] {{
        display: none !important;
    }}
    [data-testid="stActionButtons"] {{
        display:none !important;
    }}

    header[data-testid="stHeader"] {{
        display:none !important;
    }}

    body {{
        background:#F7F7FD;
    }}

    /* ===== HEADER ===== */
    .header-box {{
        background:{HEADER_GRADIENT};
        padding:40px 50px;
        border-radius:0 0 28px 28px;
        box-shadow:0 15px 45px rgba(80,48,157,0.35);
        display:flex;
        justify-content:space-between;
        align-items:center;
        width:100%;
    }}
    .header-title {{
        font-size:36px;
        font-weight:800;
        color:white;
    }}

    .header-logo-img {{
        height:60px;
    }}

    /* ===== FORM CONTAINER ===== */
    .login-card {{
        background:white;
        margin:40px auto;
        width:85%;
        padding:40px;
        border-radius:16px;
        box-shadow:0 6px 18px rgba(0,0,0,0.08);
    }}

    /* ===== BUTTONS ===== */

    /* Sign In */
    .primary-btn {{
        background:{HEADER_GRADIENT} !important;
        color:white !important;
        border:none;
        padding:16px;
        width:100%;
        border-radius:12px;
        font-size:18px;
        font-weight:700;
        box-shadow:0 6px 22px rgba(80,48,157,0.45);
        transition:0.22s ease-in-out;
    }}
    .primary-btn:hover {{
        opacity:0.90;
        transform:translateY(-1px);
    }}

    /* Bottom buttons */
    .footer-actions {{
        display:flex;
        gap:24px;
        justify-content:center;
        margin-top:30px;
        margin-bottom:50px;
    }}

    .secondary-btn {{
        background:{HEADER_GRADIENT} !important;
        color:white !important;
        border:none;
        padding:14px 20px;
        width:230px;
        border-radius:12px;
        font-size:16px;
        font-weight:700;
        text-align:center;
        box-shadow:0 6px 22px rgba(80,48,157,0.45);
        transition:0.22s ease-in-out;
    }}

    .secondary-btn:hover {{
        opacity:0.92;
        transform:translateY(-1px);
    }}

    @media(max-width:650px){{
        .footer-actions {{
            flex-direction:column;
            width:85%;
            gap:14px;
        }}
        .secondary-btn {{
            width:100%;
        }}
        .login-card {{
            width:92%;
        }}
        .header-title {{
            font-size:26px;
        }}
    }}

    </style>
    """, unsafe_allow_html=True)


# ================= LOGIN VIEW =================
def render_login_view():
    conn = get_fast_connection()

    st.markdown("<div class='login-card'>", unsafe_allow_html=True)
    with st.form("conf_login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        b = st.form_submit_button("Sign In →", type="primary")
        if b:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id,name,password_hash FROM conference_users WHERE email=%s",(email,))
            rec = cur.fetchone()
            if rec and check_password(password, rec["password_hash"]):
                st.session_state['user_id'] = rec["id"]
                st.session_state['logged_in'] = True
                st.session_state['current_page'] = 'conference_dashboard'
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='footer-actions'>
        <button class='secondary-btn' id='reg-btn'>New Registration</button>
        <button class='secondary-btn' id='fp-btn'>Forgot Password?</button>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Hidden_Register", key="reg", help="", on_click=lambda: set_auth_view("register")):
        pass
    if st.button("Hidden_FP", key="fp", help="", on_click=lambda: set_auth_view("forgot_password")):
        pass


# ================= FORGOT + REGISTER (same) =================
def render_register_view():
    st.info("Registration Page Here → same logic")
    if st.button("← Back"):
        set_auth_view("login")


def render_forgot_password_view():
    st.info("Forgot Password Page Here")
    if st.button("← Back"):
        set_auth_view("login")


# ================= MAIN =================
def render_conference_login_page():

    inject_css()

    if 'conf_auth_view' not in st.session_state:
        st.session_state['conf_auth_view'] = 'login'

    view = st.session_state['conf_auth_view']

    # ===== HEADER =====
    logo_base64 = _get_image_base64(LOGO_PATH)
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="header-logo-img">' if logo_base64 else LOGO_PLACEHOLDER_TEXT

    header_title = {
        "login": "CONFERENCE BOOKING",
        "register": "NEW REGISTRATION",
        "forgot_password": "RESET PASSWORD",
    }[view]

    st.markdown(
        f"""
        <div class="header-box">
            <div class="header-title">{header_title}</div>
            <div>{logo_html}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if view == 'login':
        render_login_view()
    elif view == 'register':
        render_register_view()
    elif view == 'forgot_password':
        render_forgot_password_view()
