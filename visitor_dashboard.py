import streamlit as st
import mysql.connector
from datetime import datetime
import json
import boto3
from botocore.exceptions import ClientError

# ======================================================
# AWS + DB CONFIG
# ======================================================

AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

HEADER_GRADIENT = "linear-gradient(90deg, #4B2ECF, #7A42FF)"
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"


# ---------------- AWS Secret ----------------
@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    secret = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(secret["SecretString"])


# ---------------- MySQL Connection ----------------
@st.cache_resource
def get_conn():
    creds = get_credentials()
    return mysql.connector.connect(
        host=creds["DB_HOST"],
        user=creds["DB_USER"],
        password=creds["DB_PASSWORD"],
        database=creds["DB_NAME"],
        autocommit=True
    )


# ======================================================
# CSS → Premium UI
# ======================================================

def load_css():
    st.markdown(f"""
    <style>

    .stApp > header {{visibility: hidden;}}

    /* HEADER */
    .header-box {{
        background: {HEADER_GRADIENT};
        padding: 34px 45px;
        border-radius: 14px;
        margin: 0 auto 40px auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 6px 25px rgba(0,0,0,0.18);
    }}

    .header-title {{
        font-size: 42px;
        font-weight: 900;
        color: white;
        letter-spacing: -0.5px;
    }}

    .header-logo {{
        height: 60px;
    }}

    /* BUTTON (Matches Header Gradient) */
    .stButton > button {{
        background: {HEADER_GRADIENT} !important;
        color: white !important;
        border-radius: 12px !important;
        font-size: 20px !important;
        padding: 16px !important;
        font-weight: 700 !important;
        border: none !important;
        width: 100%;
        box-shadow: 0 4px 14px rgba(79,73,255,0.35);
    }}

    .stButton > button:hover {{
        opacity: 0.92 !important;
        transform: scale(1.01);
    }}

    /* Visitor Table */
    .table-header {{
        font-weight: 800;
        font-size: 18px;
        margin-top: 20px;
        color: #333;
        padding-bottom: 10px;
    }}

    .data-row {{
        padding: 12px 0;
        border-bottom: 1px solid #EEE;
    }}

    .checkout-btn {{
        background: #29B573 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 6px 14px !important;
        font-weight: 600 !important;
        border: none !important;
        width: 100%;
    }}

    .completed-box {{
        background: #E4FFEE;
        padding: 6px 14px;
        border-radius: 8px;
        text-align: center;
        font-weight: 600;
        color: #1A8A4A;
    }}

    </style>
    """, unsafe_allow_html=True)


# ======================================================
# Header
# ======================================================

def render_header():
    st.markdown(f"""
        <div class="header-box">
            <div class="header-title">Welcome, {st.session_state.get("company_name","Company")}</div>
            <img src="{LOGO_URL}" class="header-logo">
        </div>
    """, unsafe_allow_html=True)


# ======================================================
# Fetch Visitors
# ======================================================

def get_visitors(company_id):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT visitor_id, full_name, phone_number, visit_type, person_to_meet,
               registration_timestamp, checkout_time
        FROM visitors
        WHERE company_id = %s
        ORDER BY registration_timestamp DESC
    """, (company_id,))

    return cursor.fetchall()


# ======================================================
# Checkout
# ======================================================

def mark_checkout(visitor_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE visitors SET checkout_time=%s WHERE visitor_id=%s",
        (datetime.now(), visitor_id)
    )


# ======================================================
# Main Dashboard
# ======================================================

def render_visitor_dashboard():

    if "admin_logged_in" not in st.session_state or not st.session_state["admin_logged_in"]:
        st.error("Access Denied")
        st.stop()

    load_css()
    render_header()

    company_id = st.session_state.get("company_id")

    # NEW VISITOR BUTTON
    st.button("➕ NEW VISITOR REGISTRATION")

    st.markdown("## 🧾 Visitor List")

    # Fetch all visitors
    visitors = get_visitors(company_id)

    if not visitors:
        st.info("No visitors yet.")
        return

    # Header Row
    table_header = st.columns([3, 2, 2, 3, 2, 2])
    table_header[0].markdown("### Name")
    table_header[1].markdown("### Phone")
    table_header[2].markdown("### Meeting")
    table_header[3].markdown("### Visited")
    table_header[4].markdown("### Checkout")
    table_header[5].markdown("### Action")

    st.markdown("---")

    # Visitor Rows
    for v in visitors:

        vid = v["visitor_id"]
        checkout_time = (
            v["checkout_time"].strftime("%d-%m-%Y %H:%M")
            if v["checkout_time"] else "—"
        )

        row = st.columns([3, 2, 2, 3, 2, 2])

        row[0].write(v["full_name"])
        row[1].write(v["phone_number"])
        row[2].write(v["person_to_meet"])
        row[3].write(v["registration_timestamp"].strftime("%d-%m-%Y %H:%M"))
        row[4].write(checkout_time)

        # Only checkout button if not completed
        with row[5]:
            if not v["checkout_time"]:
                if st.button("Checkout", key=f"checkout_{vid}", help="Mark visitor checkout"):
                    mark_checkout(vid)
                    st.rerun()
            else:
                st.markdown(f"<div class='completed-box'>Completed</div>", unsafe_allow_html=True)


# EXPORT
def render_dashboard():
    return render_visitor_dashboard()


# Manual Test
if __name__ == "__main__":
    st.session_state["admin_logged_in"] = True
    st.session_state["company_name"] = "Zodopt"
    st.session_state["company_id"] = 1
    render_visitor_dashboard()
