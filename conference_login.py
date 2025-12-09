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
# PASSWORD HELPERS
# ==============================
def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ==============================
# CSS (NO CARDS, JUST CLEAN FORM)
# ==============================
def inject_css():
    st.markdown(f"""
    <style>
    /* Remove Streamlit chrome */
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="baseMenuButton"],
    [data-testid="helpButton"],
    [data-testid="collapsedControl"],
    [data-testid="stStatusWidget"],
    [data-testid="stActionButtons"] {{
        display:none !important;
    }}

    .block-container {{
        padding-top:0 !important;
        max-width:100% !important;
    }}

    body {{
        background:#FBFCFF;
        font-family:'Inter',sans-serif;
    }}

    /* Header */
    .header-bar {{
        width:100%;
        background:{HEADER_GRADIENT};
        padding:34px 48px;
        border-radius:0 0 26px 26px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 10px 32px rgba(0,0,0,0.18);
    }}

    .header-title {{
        font-size:30px;
        font-weight:800;
        color:white;
    }}

    .header-logo {{
        height:56px;
    }}

    /* Centered form – NO container background */
    .form-wrapper {{
        max-width:480px;
        margin:60px auto 0 auto;
    }}

    .stTextInput > div > div > input {{
        background:#F1F3FA !important;
        border-radius:10px !important;
        padding:14px !important;
        font-size:16px !important;
    }}

    /* Style all buttons */
    .stForm button {{
        background:{HEADER_GRADIENT} !important;
        color:white !important;
        border:none !important;
        border-radius:11px !important;
        padding:14px !important;
        font-size:16px !important;
        font-weight:700 !important;
        width:100% !important;
        box-shadow:0 6px 22px rgba(80,48,157,0.35) !important;
    }}

    .stForm button:hover {{
        opacity:0.93;
        transform:translateY(-1px);
    }}

    .footer-buttons {{
        max-width:480px;
        margin:26px auto 60px auto;
        display:flex;
        gap:16px;
    }}

    .footer-buttons .stButton > button {{
        background:{HEADER_GRADIENT} !important;
        color:white !important;
        border:none !important;
        border-radius:11px !important;
        padding:12px !important;
        font-size:15px !important;
        font-weight:700 !important;
        width:100% !important;
        box-shadow:0 5px 18px rgba(80,48,157,0.35) !important;
    }}

    .footer-buttons .stButton > button:hover {{
        opacity:0.93;
        transform:translateY(-1px);
    }}

    @media (max-width: 600px) {{
        .form-wrapper {{
            margin-top:40px;
            padding:0 14px;
        }}
        .footer-buttons {{
            flex-direction:column;
            padding:0 14px;
        }}
        .header-title {{
            font-size:22px;
        }}
        .header-logo {{
            height:46px;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)


# ==============================
# LOGIN VIEW (ONLY UI YOU SEE NOW)
# ==============================
def render_login_view():
    conn = get_connection()

    st.markdown("<div class='form-wrapper'>", unsafe_allow_html=True)

    with st.form("conf-login-form"):
        email = st.text_input("Email")
        pwd = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In →")

        if submitted:
            if not email or not pwd:
                st.error("Please enter both email and password.")
            else:
                cur = conn.cursor(dictionary=True)
                cur.execute(
                    "SELECT id,name,password_hash FROM conference_users "
                    "WHERE email=%s AND is_active=1",
                    (email,),
                )
                user = cur.fetchone()
                if user and verify_password(pwd, user["password_hash"]):
                    st.session_state["user_id"] = user["id"]
                    st.session_state["current_page"] = "conference_dashboard"
                    st.session_state["conf_auth_view"] = "login"
                    st.success("Login successful")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

    st.markdown("</div>", unsafe_allow_html=True)

    # Footer actions
    st.markdown("<div class='footer-buttons'>", unsafe_allow_html=True)
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


# ==============================
# SIMPLE PLACEHOLDER VIEWS
# (You can replace with real forms later)
# ==============================
def render_register_view():
    st.write("Registration screen (to be implemented).")
    if st.button("← Back to Login"):
        st.session_state["conf_auth_view"] = "login"
        st.rerun()


def render_forgot_view():
    st.write("Forgot password screen (to be implemented).")
    if st.button("← Back to Login"):
        st.session_state["conf_auth_view"] = "login"
        st.rerun()


# ==============================
# PUBLIC ENTRYPOINT
# ==============================
def render_conference_login_page():
    inject_css()

    # Initialize view state
    if "conf_auth_view" not in st.session_state:
        st.session_state["conf_auth_view"] = "login"

    # Header
    st.markdown(
        f"""
        <div class="header-bar">
            <div class="header-title">Conference Booking Login</div>
            <img src="{LOGO_URL}" class="header-logo">
        </div>
        """,
        unsafe_allow_html=True,
    )

    view = st.session_state["conf_auth_view"]

    if view == "login":
        render_login_view()
    elif view == "register":
        render_register_view()
    else:
        render_forgot_view()
