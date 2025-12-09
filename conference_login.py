import streamlit as st
import boto3
import json
import mysql.connector
import bcrypt

AWS_REGION = "ap-south-1"
AWS_SECRET = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
GRADIENT = "linear-gradient(90deg,#50309D,#7A42FF)"


@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    res = client.get_secret_value(SecretId=AWS_SECRET)
    return json.loads(res["SecretString"])


@st.cache_resource
def get_conn():
    c = get_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True
    )


def check_pwd(p, h):
    try:
        return bcrypt.checkpw(p.encode(), h.encode())
    except Exception:
        return False


def inject_css():
    st.markdown(f"""
    <style>
    /* Remove Streamlit chrome */
    header, [data-testid="stToolbar"], .st-emotion-cache-1dp5vir, 
    [data-testid="stDecoration"], [data-testid="stStatusWidget"],
    [data-testid="baseMenuButton"], footer {{
        display:none !important;
    }}

    .block-container {{
        padding-top:0 !important;
        max-width:100% !important;
    }}

    .page-wrapper {{
        display:flex;
        flex-direction:column;
        min-height:100vh;
        background:#FBFCFF;
        font-family:'Inter',sans-serif;
    }}

    .header-bar {{
        width:100%;
        background:{GRADIENT};
        padding:28px 42px;
        border-radius:0 0 22px 22px;
        box-shadow:0 8px 28px rgba(0,0,0,0.18);
        display:flex;
        justify-content:space-between;
        align-items:center;
    }}

    .header-title {{
        font-size:28px;
        font-weight:800;
        color:#fff;
    }}
    .header-logo {{
        height:55px;
    }}

    /* Form wrapper */
    .login-form {{
        max-width:450px;
        margin:60px auto 0 auto;
        padding:0 16px;
    }}

    .stTextInput input {{
        background:#EFF1F7 !important;
        border-radius:10px !important;
        padding:14px !important;
        font-size:16px !important;
    }}

    .stForm button {{
        background:{GRADIENT} !important;
        color:#fff !important;
        border:none !important;
        border-radius:10px !important;
        padding:14px !important;
        font-size:16px !important;
        font-weight:700 !important;
        width:100% !important;
        margin-top:12px !important;
        box-shadow:0 6px 20px rgba(80,48,157,0.35);
    }}

    .footer-actions {{
        max-width:450px;
        margin:24px auto 40px auto;
        display:flex;
        justify-content:space-between;
        gap:14px;
        padding:0 16px;
    }}

    .footer-actions button {{
        background:#FFFFFF !important;
        color:#50309D !important;
        font-weight:700 !important;
        border:2px solid #50309D !important;
        border-radius:10px !important;
        padding:12px !important;
        width:100% !important;
    }}

    @media(max-width:600px){{
        .header-title {{ font-size:22px; }}
        .header-bar {{ padding:22px; }}
        .header-logo {{ height:44px; }}
        .footer-actions {{ flex-direction:column; }}
    }}
    </style>
    """, unsafe_allow_html=True)


def render_login():
    inject_css()
    conn = get_conn()

    st.markdown("<div class='page-wrapper'>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class='header-bar'>
            <div class='header-title'>Conference Login</div>
            <img class='header-logo' src="{LOGO_URL}">
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div class='login-form'>", unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In →")

        if submit:
            if not email or not password:
                st.error("Enter email and password")
            else:
                cur = conn.cursor(dictionary=True)
                cur.execute(
                    "SELECT id,name,password_hash FROM conference_users WHERE email=%s AND is_active=1",
                    (email,),
                )
                usr = cur.fetchone()
                if usr and check_pwd(password, usr["password_hash"]):
                    st.session_state["user_id"] = usr["id"]
                    st.session_state["current_page"] = "conference_dashboard"
                    st.success("Login successful")
                    st.rerun()
                else:
                    st.error("Invalid email or password")

    st.markdown("</div>", unsafe_allow_html=True)

    # Footer buttons
    st.markdown("<div class='footer-actions'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("New Registration"):
            st.session_state["conf_auth_view"] = "register"
            st.rerun()
    with c2:
        if st.button("Forgot Password?"):
            st.session_state["conf_auth_view"] = "forgot"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# Entry point
def render_conference_login_page():
    if "conf_auth_view" not in st.session_state:
        st.session_state["conf_auth_view"] = "login"

    if st.session_state["conf_auth_view"] == "login":
        render_login()
    elif st.session_state["conf_auth_view"] == "register":
        st.write("Register page here")
    else:
        st.write("Forgot password page here")
