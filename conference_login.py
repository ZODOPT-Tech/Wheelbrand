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
# PASSWORD SECURITY
# ==============================
def verify_password(input_password, db_hash):
    return bcrypt.checkpw(input_password.encode(), db_hash.encode())


# ==============================
# CSS
# ==============================
def inject_css():
    st.markdown(f"""
    <style>

    /* Layout reset */
    .block-container {{
        padding: 0 !important;
        max-width: 100% !important;
    }}

    body {{
        background: #F6F8FF;
        font-family: 'Inter', sans-serif;
    }}

    /* Remove Streamlit UI */
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="helpButton"],
    [data-testid="collapsedControl"],
    [data-testid="baseMenuButton"] {{
        display:none !important;
    }}

    /* Header section */
    .header-box {{
        width: 100%;
        background:{HEADER_GRADIENT};
        padding: 30px 42px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        border-radius:0 0 26px 26px;
        box-shadow:0 6px 22px rgba(0,0,0,0.18);
    }}

    .header-title {{
        color:white;
        font-size:32px;
        font-weight:900;
    }}

    .logo {{
        height:55px;
    }}

    /* Login card box */
    .login-card {{
        width:440px;
        margin:70px auto;
        background:white;
        border-radius:18px;
        padding:34px 30px;
        box-shadow:0 4px 18px rgba(0,0,0,0.08);
    }}

    .stTextInput > div > div > input {{
        background:#F2F4FA;
        padding:14px;
        border-radius:10px;
        font-size:16px;
    }}

    /* Main button */
    .primary-btn {{
        background:{HEADER_GRADIENT} !important;
        color:white !important;
        font-weight:700 !important;
        border:none !important;
        padding:14px !important;
        width:100%;
        border-radius:12px !important;
        font-size:16px !important;
        margin-top:10px !important;
        box-shadow:0 6px 22px rgba(80,48,157,0.4) !important;
    }}

    .primary-btn:hover {{
        opacity:0.93;
        transform:translateY(-1px);
    }}

    /* Footer buttons */
    .footer-box {{
        width:440px;
        margin:0 auto 70px auto;
        display:flex;
        justify-content:space-between;
        gap:16px;
    }}

    .footer-btn {{
        background:{HEADER_GRADIENT};
        color:white;
        width:50%;
        padding:12px;
        border-radius:12px;
        text-align:center;
        font-weight:700;
        box-shadow:0 6px 20px rgba(80,48,157,0.4);
    }}

    @media(max-width:600px) {{
        .login-card {{
            width:92%;
        }}
        .footer-box {{
            width:92%;
            flex-direction:column;
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
# LOGIN FLOW
# ==============================
def render_login_view():
    conn = get_connection()

    with st.container():
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        with st.form("login"):
            email = st.text_input("Email")
            pwd = st.text_input("Password", type="password")

            if st.form_submit_button("Sign In →", type="primary", use_container_width=True):
                if not email or not pwd:
                    st.error("Enter email and password")
                else:
                    cur = conn.cursor(dictionary=True)
                    cur.execute("SELECT id,name,password_hash FROM conference_users WHERE email=%s AND is_active=1", (email,))
                    user = cur.fetchone()

                    if user and verify_password(pwd, user['password_hash']):
                        st.session_state['user_id'] = user['id']
                        st.session_state['current_page'] = "conference_dashboard"
                        st.rerun()
                    else:
                        st.error("Invalid login details")

        st.markdown("</div>", unsafe_allow_html=True)

    # Footer buttons
    st.markdown("<div class='footer-box'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Registration", use_container_width=True):
            st.session_state['conf_auth_view'] = 'register'
            st.rerun()
    with col2:
        if st.button("Forgot Password?", use_container_width=True):
            st.session_state['conf_auth_view'] = 'forgot_password'
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ==============================
# PLACEHOLDER PAGES
# (You can style later)
# ==============================
def render_register_view():
    st.write("Registration Page")


def render_forgot_view():
    st.write("Forgot Password Page")


# ==============================
# ROUTER
# ==============================
def render_conference_login_page():
    inject_css()

    if 'conf_auth_view' not in st.session_state:
        st.session_state['conf_auth_view'] = 'login'

    # Header
    st.markdown(f"""
    <div class='header-box'>
        <div class='header-title'>Conference Login</div>
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
