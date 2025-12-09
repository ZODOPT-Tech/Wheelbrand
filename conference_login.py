import streamlit as st
import mysql.connector
import boto3
import json
import bcrypt
import base64
import traceback

# ==============================
# CONFIG
# ==============================
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"
LOGO_PATH = "zodopt.png"


# ==============================
# AWS & DB
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
# SECURITY HELPERS
# ==============================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()


def check_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed_password.encode())
    except:
        return False


def set_view(v: str):
    st.session_state.conf_auth_view = v
    st.rerun()


def load_logo_base64():
    try:
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""


# ==============================
# GLOBAL CSS
# ==============================
def inject_css():
    st.markdown(f"""
    <style>

    /* Remove Streamlit Header & Toolbar */
    [data-testid="stToolbar"], [data-testid="stActionButtons"], header, footer {{
        display: none !important;
        visibility: hidden !important;
    }}

    .block-container {{
        padding-top: 0 !important;
        margin-top: -3rem !important;
        background: transparent !important;
        max-width: 900px !important;
    }}

    /* Header */
    .header-box {{
        background: {HEADER_GRADIENT};
        margin: 0 -2rem 2rem -2rem;
        padding: 32px 48px;
        border-radius:0 0 22px 22px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.25);
        display:flex;
        justify-content:space-between;
        align-items:center;
    }}

    .header-title {{
        font-size: 34px;
        font-weight: 900;
        color: white;
        margin: 0;
        line-height: 1.3;
    }}

    .logo-img {{
        height: 58px;
    }}

    /* Remove white card wrapper */
    div[data-testid="stForm"], div[data-baseweb="card"] {{
        background: transparent !important;
        box-shadow: none !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }}

    /* Inputs */
    .stTextInput > div > input,
    .stSelectbox div[data-baseweb="select"] {{
        background: #F4F1FF;
        border: none;
        padding: 14px;
        border-radius: 10px;
        font-size: 16px;
    }}

    /* Primary Buttons */
    .stForm button[kind="primary"], .primary-btn {{
        background: {HEADER_GRADIENT} !important;
        border:none !important;
        color:white !important;
        border-radius:10px !important;
        padding:12px !important;
        font-size:16px !important;
        font-weight:700 !important;
        width:100% !important;
        box-shadow:0 4px 12px rgba(0,0,0,0.15);
    }}

    /* Secondary Buttons */
    .secondary-btn {{
        background:white !important;
        border:2px solid #50309D !important;
        color:#50309D !important;
        border-radius:10px;
        padding:10px;
        font-size:15px;
        width:100%;
        font-weight:700;
    }}

    /* Responsive layout for footer buttons */
    .footer-actions {{
        display:flex;
        gap:20px;
        margin-top:24px;
    }}

    @media(max-width: 600px){{
        .footer-actions {{
            flex-direction:column;
        }}
        .header-box {{
            padding: 24px 24px;
            margin-left:-1rem;
            margin-right:-1rem;
        }}
        .header-title {{
            font-size:26px;
        }}
        .logo-img {{
            height:48px;
        }}
    }}

    </style>
    """, unsafe_allow_html=True)


# ==============================
# LOGIN VIEW
# ==============================
def render_login():
    conn = get_conn()
    with st.form("login_form"):
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In →", type="primary")

        if submit:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id,name,password_hash FROM conference_users WHERE email=%s AND is_active=TRUE", (email,))
            u = cur.fetchone()
            if u and check_password(pw, u["password_hash"]):
                st.session_state.user_id = u["id"]
                st.session_state.current_page = "conference_dashboard"
                st.rerun()
            else:
                st.error("Invalid Email or Password")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.button("New Registration", use_container_width=True, on_click=lambda: set_view("register"), key="new_reg", type="secondary")
    with col2:
        st.button("Forgot Password?", use_container_width=True, on_click=lambda: set_view("forgot"), key="forgot", type="secondary")


# ==============================
# REGISTER VIEW
# ==============================
def render_register():
    conn = get_conn()
    with st.form("reg_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        company = st.text_input("Company")
        dept = st.selectbox("Department", ["SELECT", "SALES","HR","FINANCE","DELIVERY/TECH","DIGITAL MARKETING","IT"])
        pw = st.text_input("Password", type="password")
        cpw = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Create Account →", type="primary")

        if submit:
            if not all([name,email,company,pw,cpw]) or dept=="SELECT":
                st.error("All fields required")
            elif pw != cpw:
                st.error("Passwords do not match")
            else:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM conference_users WHERE email=%s",(email,))
                if cur.fetchone()[0]>0:
                    st.error("Email exists")
                else:
                    cur.execute(
                        "INSERT INTO conference_users(name,email,company,department,password_hash) VALUES(%s,%s,%s,%s,%s)",
                        (name,email,company,dept,hash_password(pw))
                    )
                    st.success("Registration complete")
                    set_view("login")

    st.divider()
    st.button("Back to Login", use_container_width=True, on_click=lambda: set_view("login"), key="reg_back", type="secondary")


# ==============================
# FORGOT PASSWORD VIEW
# ==============================
def render_forgot():
    conn = get_conn()

    email = st.text_input("Enter your registered Email")
    new_pw = st.text_input("New Password", type="password")
    cpw = st.text_input("Confirm New Password", type="password")

    if st.button("Reset Password →", type="primary"):
        if new_pw!=cpw or len(new_pw)<8:
            st.error("Passwords mismatch or too short")
        else:
            cur = conn.cursor()
            cur.execute("UPDATE conference_users SET password_hash=%s WHERE email=%s",(hash_password(new_pw),email))
            st.success("Password reset successful")
            set_view("login")

    st.divider()
    st.button("Back", use_container_width=True, on_click=lambda: set_view("login"), key="forgot_back", type="secondary")


# ==============================
# MAIN LOGIN PAGE
# ==============================
def render_conference_login_page():
    inject_css()

    if "conf_auth_view" not in st.session_state:
        st.session_state.conf_auth_view = "login"

    view = st.session_state.conf_auth_view

    # HEADER
    logo_b64 = load_logo_base64()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="logo-img">' if logo_b64 else "<b>ZODOPT</b>"

    title = {
        "login": "CONFERENCE BOOKING - SIGN IN",
        "register": "NEW REGISTRATION",
        "forgot": "RESET PASSWORD"
    }[view]

    st.markdown(f"""
    <div class="header-box">
        <div class="header-title">{title}</div>
        {logo_html}
    </div>
    """, unsafe_allow_html=True)

    if view=="login":
        render_login()
    elif view=="register":
        render_register()
    elif view=="forgot":
        render_forgot()
