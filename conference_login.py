import streamlit as st
import os
import base64
import mysql.connector
import bcrypt
import boto3
import json
import traceback

# =======================================================================
# CONFIG
# =======================================================================
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
LOGO_PATH = "zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


# =======================================================================
# SECRETS MANAGER
# =======================================================================
@st.cache_resource
def get_db_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(resp["SecretString"])


@st.cache_resource
def get_db_conn():
    c = get_db_credentials()
    conn = mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True
    )
    return conn


# =======================================================================
# SECURITY
# =======================================================================
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


# =======================================================================
# UTILS
# =======================================================================
def img_base64(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def switch_view(view):
    st.session_state["conf_auth_view"] = view
    st.rerun()


# =======================================================================
# GLOBAL CSS (DASHBOARD + HIDE TOOLBAR)
# =======================================================================
def inject_css():
    st.markdown(f"""
    <style>

    /* ===== GLOBAL RESET ===== */
    .stApp > header {{
        display:none !important;
    }}
    .block-container {{
        padding-top:0 !important;
        margin-top:-2rem !important;
    }}

    /* ===== FULL-WIDTH HEADER ===== */
    .header-box {{
        background:{HEADER_GRADIENT};
        margin:0 -2rem 2rem -2rem;
        padding:28px 40px;
        border-radius:0 0 20px 20px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 6px 20px rgba(0,0,0,0.18);
    }}

    .header-title {{
        font-size:32px;
        font-weight:900;
        color:white;
        margin:0;
    }}
    .header-logo-img {{
        height:60px;
    }}

    /* ===== CENTER CONTAINER ===== */
    .form-container {{
        max-width:460px;
        margin:0 auto;
    }}

    /* ===== INPUTS ===== */
    .stTextInput > div > input,
    .stSelectbox div[data-baseweb="select"] {{
        background:#f6f4ff;
        border:1px solid #ddd;
        padding:13px;
        border-radius:10px;
        font-size:15px;
    }}

    /* ===== BUTTONS ===== */
    .stForm button[kind="primary"],
    .stButton > button:not([key*="back"]) {{
        background:{HEADER_GRADIENT} !important;
        border:none !important;
        color:white !important;
        font-weight:700 !important;
        border-radius:10px !important;
        width:100% !important;
        font-size:15px !important;
        padding:10px 20px !important;
        box-shadow:0 3px 12px rgba(0,0,0,0.15) !important;
    }}

    .stButton > button[key*="back"],
    .stButton > button[key*="forgot"],
    .stButton > button[key*="new_reg"] {{
        background:white !important;
        color:#50309D !important;
        border:2px solid #50309D !important;
        border-radius:10px !important;
        width:100% !important;
        font-weight:600 !important;
        font-size:14px !important;
        padding:9px 18px !important;
    }}

    /* ===== HIDE STREAMLIT FLOATING TOOLBAR ===== */
    [data-testid="stToolbar"] {{ display:none !important; }}
    [data-testid="stActionButtons"] {{ display:none !important; }}
    [data-testid="collapsedControl"] {{ display:none !important; }}
    [data-testid="stStatusWidget"] {{ display:none !important; }}
    [data-testid="baseMenuButton"] {{ display:none !important; }}
    [title="View code"] {{ display:none !important; }}
    [title="Manage app settings"] {{ display:none !important; }}
    </style>
    """, unsafe_allow_html=True)


# =======================================================================
# LOGIN VIEW
# =======================================================================
def login_view():
    conn = get_db_conn()

    st.markdown("<div class='form-container'>", unsafe_allow_html=True)

    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In →")

        if submit:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id,name,password_hash FROM conference_users WHERE email=%s AND is_active=1", (email,))
            user = cur.fetchone()
            if user and check_password(password, user["password_hash"]):
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = user["id"]
                st.session_state["user_email"] = email
                st.session_state["user_name"] = user["name"]
                st.session_state["current_page"] = "conference_dashboard"
                st.rerun()
            else:
                st.error("Invalid Email or Password")

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("New Registration", key="new_reg"):
            switch_view("register")
    with c2:
        if st.button("Forgot Password?", key="forgot"):
            switch_view("forgot")

    st.markdown("</div>", unsafe_allow_html=True)


# =======================================================================
# REGISTER VIEW
# =======================================================================
def register_view():
    conn = get_db_conn()
    st.markdown("<div class='form-container'>", unsafe_allow_html=True)

    deps = ["SELECT","SALES","HR","FINANCE","DELIVERY/TECH","DIGITAL MARKETING","IT"]

    with st.form("reg"):
        name = st.text_input("Name")
        email = st.text_input("Email ID")
        company = st.text_input("Company")
        department = st.selectbox("Department", deps)
        pw = st.text_input("Password", type="password")
        cp = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register")

        if submit:
            if not all([name,email,company,pw,cp]):
                st.error("Fill all fields")
            elif pw!=cp:
                st.error("Password mismatch")
            elif department=="SELECT":
                st.error("Select department")
            else:
                cur = conn.cursor()
                cur.execute("SELECT count(*) FROM conference_users WHERE email=%s", (email,))
                if cur.fetchone()[0]>0:
                    st.error("Email exists")
                else:
                    cur.execute(
                        "INSERT INTO conference_users(name,email,company,department,password_hash) VALUES(%s,%s,%s,%s,%s)",
                        (name,email,company,department,hash_password(pw))
                    )
                    st.success("Registered Successfully")
                    switch_view("login")

    st.write("")
    if st.button("← Back", key="back_reg"):
        switch_view("login")

    st.markdown("</div>", unsafe_allow_html=True)


# =======================================================================
# FORGOT VIEW
# =======================================================================
def forgot_view():
    conn = get_db_conn()
    st.markdown("<div class='form-container'>", unsafe_allow_html=True)

    if "reset_email" not in st.session_state:
        st.session_state["reset_email"] = None

    if st.session_state["reset_email"] is None:
        with st.form("email_check"):
            email = st.text_input("Enter Email")
            submit = st.form_submit_button("Search")

            if submit:
                cur = conn.cursor()
                cur.execute("SELECT id FROM conference_users WHERE email=%s", (email,))
                if cur.fetchone():
                    st.session_state["reset_email"] = email
                    st.rerun()
                else:
                    st.error("Email not found")
    else:
        st.write(f"Resetting password for: {st.session_state['reset_email']}")
        with st.form("reset"):
            pw = st.text_input("New Password", type="password")
            cp = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Change Password")

            if submit:
                if pw!=cp:
                    st.error("Mismatch")
                else:
                    cur = conn.cursor()
                    cur.execute("UPDATE conference_users SET password_hash=%s WHERE email=%s",
                                (hash_password(pw), st.session_state["reset_email"]))
                    st.success("Updated")
                    st.session_state["reset_email"] = None
                    switch_view("login")

    st.write("")
    if st.button("← Back", key="back_forgot"):
        st.session_state["reset_email"] = None
        switch_view("login")

    st.markdown("</div>", unsafe_allow_html=True)


# =======================================================================
# MAIN ENTRY
# =======================================================================
def render_conference_login_page():
    inject_css()

    view = st.session_state.get("conf_auth_view", "login")

    logo_b64 = img_base64(LOGO_PATH)
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" class="header-logo-img">'
        if logo_b64 else
        '<div style="color:white;font-size:22px;font-weight:700">ZODOPT</div>'
    )

    title = (
        "CONFERENCE BOOKING - LOGIN" if view=="login"
        else "NEW REGISTRATION" if view=="register"
        else "RESET PASSWORD"
    )

    st.markdown(f"""
        <div class="header-box">
            <div class="header-title">{title}</div>
            {logo_html}
        </div>
    """, unsafe_allow_html=True)

    if view=="login":
        login_view()
    elif view=="register":
        register_view()
    else:
        forgot_view()
