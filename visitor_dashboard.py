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
# CSS
# ======================================================

def load_css():
    st.markdown(f"""
    <style>
    .stApp > header {{visibility: hidden;}}

    .header-box {{
        background: {HEADER_GRADIENT};
        padding: 26px 45px;
        border-radius: 12px;
        max-width: 1600px;
        width: 100%;
        margin: 0 auto 35px auto;

        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0px 4px 22px rgba(0,0,0,0.25);
    }}

    .header-title {{
        font-size: 38px;
        font-weight: 800;
        color: white;
    }}

    .header-logo {{
        height: 55px;
    }}

    .dash-card {{
        background: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 25px;
    }}

    .visitor-header-row {{
        font-weight: 700;
        color: #333;
        margin-top: 15px;
    }}

    .action-btn {{
        background: #4B2ECF !important;
        color: white !important;
        padding: 8px 15px !important;
        border-radius: 8px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        border: none !important;
        width: 100%;
    }}

    </style>
    """, unsafe_allow_html=True)


# ======================================================
# Header Section
# ======================================================

def render_header():
    st.markdown(f"""
        <div class="header-box">
            <div class="header-title">VISITOR MANAGEMENT DASHBOARD</div>
            <img src="{LOGO_URL}" class="header-logo">
        </div>
    """, unsafe_allow_html=True)


# ======================================================
# Fetch Visitors for Company
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
# Checkout Visitor
# ======================================================

def mark_checkout(visitor_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE visitors SET checkout_time=%s WHERE visitor_id=%s",
        (datetime.now(), visitor_id)
    )


# ======================================================
# Visitor Dashboard Main Section
# ======================================================

def render_visitor_dashboard():

    if "admin_logged_in" not in st.session_state or not st.session_state["admin_logged_in"]:
        st.error("Access Denied")
        st.stop()

    load_css()
    render_header()

    company_name = st.session_state.get("company_name", "Your Company")
    company_id = st.session_state.get("company_id")

    # ================= WELCOME CARD =================
    st.markdown(f"""
    <div class="dash-card">
        <h2 style='margin-bottom:5px;'>Welcome, {company_name}</h2>
        <div style='font-size:17px;color:#555;'>
            Your visitor management system is active.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ================= NEW VISITOR BUTTON =================
    if st.button("➕ NEW VISITOR REGISTRATION"):
        st.session_state["current_page"] = "visitor_details"
        st.rerun()

    # ================= VISITOR LIST =================
    st.markdown("### 🧾 Visitor List")

    visitors = get_visitors(company_id)

    if not visitors:
        st.info("No visitors found yet.")
        return

    # ---- Header row ----
    header_cols = st.columns([3, 2, 2, 3, 2, 2])
    header_cols[0].markdown("**Name**")
    header_cols[1].markdown("**Phone**")
    header_cols[2].markdown("**Meeting**")
    header_cols[3].markdown("**Visited**")
    header_cols[4].markdown("**Checkout**")
    header_cols[5].markdown("**Action**")

    st.markdown("---")

    # ---- Visitor Rows ----
    for v in visitors:

        vid = v["visitor_id"]

        checkout_display = (
            v["checkout_time"].strftime("%d-%m-%Y %H:%M")
            if v["checkout_time"] else "—"
        )

        row = st.columns([3, 2, 2, 3, 2, 2])

        row[0].write(v["full_name"])
        row[1].write(v["phone_number"])
        row[2].write(v["person_to_meet"])
        row[3].write(v["registration_timestamp"].strftime("%d-%m-%Y %H:%M"))
        row[4].write(checkout_display)

        # ---- Checkout Button ONLY ----
        with row[5]:
            if not v["checkout_time"]:
                if st.button("Checkout", key=f"checkout_{vid}"):
                    mark_checkout(vid)
                    st.rerun()
            else:
                st.success("Completed")


# EXPORT FOR ROUTER
def render_dashboard():
    return render_visitor_dashboard()


# Manual Test
if __name__ == "__main__":
    st.session_state["admin_logged_in"] = True
    st.session_state["company_name"] = "Zodopt Tech Pvt Ltd"
    st.session_state["company_id"] = 1

    render_visitor_dashboard()
