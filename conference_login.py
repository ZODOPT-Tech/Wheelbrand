import streamlit as st
import boto3
import json
import mysql.connector
import bcrypt

# ==============================
# CONFIG
# ==============================
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


# ==============================
# DB CONNECTION
# ==============================
@st.cache_resource
def get_db_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(resp["SecretString"])


@st.cache_resource
def get_connection():
    c = get_db_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True
    )


# ==============================
# PASSWORD VERIFY
# ==============================
def verify_password(input_password, db_hash):
    return bcrypt.checkpw(input_password.encode(), db_hash.encode())


# ==============================
# CSS
# ==============================
def inject_css():
    st.markdown(f"""
    <style>
    
    /* Hide Streamlit chrome */
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="baseMenuButton"],
    [data-testid="helpButton"],
    [data-testid="collapsedControl"] {{
        display: none !important;
    }}

    .block-container {{
        padding-top:0 !important;
        max-width:100% !important;
    }}

    body {{
        background:#FBFCFF;
        font-family:'Inter',sans-serif;
    }}

    .header {{
        width:100%;
        background:{HEADER_GRADIENT};
        padding:40px 60px;
        border-radius:0 0 30px 30px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 10px 35px rgba(0,0,0,0.12);
    }}

    .header-title {{
        font-size:34px;
        font-weight:800;
        color:white;
    }}

    .logo {{
        height:60px;
    }}

    .form-wrapper {{
        max-width:480px;
        margin:60px auto;
        text-align:center;
    }}

    .stTextInput > div > div input {{
        font-size:16px !important;
        padding:14px !important;
        border-radius:10px !important;
        background:#F2F4FA !important;
    }}

    /* SIGN IN BUTTON */
    .primary-btn {{
        background:{HEADER_GRADIENT} !important;
        color:white !important;
        padding:14px !important;
        font-size:17px !important;
        font-weight:700 !important;
        width:100%;
        border-radius:11px !important;
        border:none !important;
        box-shadow:0 6px 22px rgba(80,48,157,0.35) !important;
        margin-top:12px !important;
    }}

    .primary-btn:hover {{
        opacity:0.93;
        transform:translateY(-2px);
    }}

    .footer-buttons {{
        max-width:480px;
        margin:30px auto;
        display:flex;
        justify-content:space-between;
        gap:18px;
    }}

    .footer-btn {{
        background:{HEADER_GRADIENT};
        flex:1;
        color:white;
        text-align:center;
        font-size:15px;
        font-weight:700;
        padding:12px;
        border-radius:10px;
        cursor:pointer;
        box-shadow:0 6px 20px rgba(80,48,157,0.32);
    }}

    .footer-btn:hover {{
        opacity:0.93;
    }}

    @media(max-width:600px){
        .footer-buttons {{
            flex-direction:column;
        }}
    }

    </style>
    """, unsafe_allow_html=True)


# ==============================
# LOGIN VIEW
# ==============================
def render_login_view():
    conn = get_connection()

    st.markdown("<div class='form-wrapper'>", unsafe_allow_html=True)

    with st.form("login-form"):
        email = st.text_input("Email")
        pwd = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In →", type="primary", use_container_width=True)

        if submit:
            if not email or not pwd:
                st.error("Enter login details")
            else:
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT id,name,password_hash FROM conference_users WHERE email=%s AND is_active=1", (email,))
                user = cur.fetchone()

                if user and verify_password(pwd, user['password_hash']):
                    st.session_state['user_id'] = user['id']
                    st.session_state['current_page'] = "conference_dashboard"
                    st.rerun()
                else:
                    st.error("Invalid email/password")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='footer-buttons'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        if st.button("New Registration", use_container_width=True):
            st.session_state['conf_auth_view'] = "register"
            st.rerun()

    with col2:
        if st.button("Forgot Password?", use_container_width=True):
            st.session_state['conf_auth_view'] = "forgot"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ==============================
# STUB VIEWS
# ==============================
def render_register_view():
    st.write("Registration Coming Soon")


def render_forgot_view():
    st.write("Reset Coming Soon")


# ==============================
# ROUTER
# ==============================
def render_conference_login_page():
    inject_css()

    if 'conf_auth_view' not in st.session_state:
        st.session_state['conf_auth_view'] = 'login'

    st.markdown(f"""
    <div class="header">
        <div class="header-title">Welcome Back</div>
        <img src="{LOGO_URL}" class="logo">
    </div>
    """, unsafe_allow_html=True)

    view = st.session_state['conf_auth_view']
    if view == "login":
        render_login_view()
    elif view == "register":
        render_register_view()
    else:
        render_forgot_view()
