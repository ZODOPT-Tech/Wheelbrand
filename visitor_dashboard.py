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
        margin: 0;
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

    .visitor-table table {{
        width: 100% !important;
        border-collapse: collapse;
        margin-top: 15px;
    }}

    .visitor-table th {{
        background: #F3F1FF;
        padding: 12px;
        text-align: left;
        font-weight: 700;
    }}

    .visitor-table td {{
        padding: 10px;
        border-bottom: 1px solid #EEE;
    }}

    .action-btn {{
        background: #4B2ECF;
        color: white;
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        border: none;
        cursor: pointer;
        margin-right: 5px;
    }}

    .reset-btn {{
        background: #D9534F !important;
    }}

    .checkout-btn {{
        background: #28a745 !important;
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
        SELECT id, full_name, phone_number, visit_type, person_to_meet,
               registration_timestamp, checkout_time
        FROM visitors
        WHERE company_id = %s
        ORDER BY registration_timestamp DESC
    """, (company_id,))

    return cursor.fetchall()


# ======================================================
# Update Checkout Time
# ======================================================

def mark_checkout(visitor_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE visitors SET checkout_time=%s WHERE id=%s",
        (datetime.now(), visitor_id)
    )


# ======================================================
# Reset Visitor Entry
# ======================================================

def reset_visitor(visitor_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM visitors WHERE id=%s", (visitor_id,))


# ======================================================
# Visitor Dashboard Main Section
# ======================================================

def render_visitor_dashboard():

    # Redirect if not logged in
    if "admin_logged_in" not in st.session_state or not st.session_state["admin_logged_in"]:
        st.error("Access Denied")
        st.stop()

    load_css()
    render_header()

    admin = st.session_state.get("admin_name", "Admin")
    company_id = st.session_state.get("company_id")

    # ================= WELCOME CARD =================
    st.markdown(f"""
    <div class="dash-card">
        <h2 style='margin-bottom:5px;'>Welcome, {admin}</h2>
        <div style='font-size:17px;color:#555;'>Company ID: <b>{company_id}</b></div>
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

    st.markdown("<div class='visitor-table'>", unsafe_allow_html=True)

    # Table Headers
    st.markdown("""
    <table>
        <tr>
            <th>Name</th>
            <th>Phone</th>
            <th>Meeting</th>
            <th>Visited</th>
            <th>Checkout</th>
            <th>Actions</th>
        </tr>
    """, unsafe_allow_html=True)

    # Table rows
    for v in visitors:
        checkout = v["checkout_time"].strftime("%d-%m-%Y %H:%M") if v["checkout_time"] else "—"

        st.markdown(f"""
        <tr>
            <td>{v['full_name']}</td>
            <td>{v['phone_number']}</td>
            <td>{v['person_to_meet']}</td>
            <td>{v['registration_timestamp'].strftime("%d-%m-%Y %H:%M")}</td>
            <td>{checkout}</td>
            <td>
                <form action="" method="get">
                    <button class="action-btn checkout-btn" name="checkout_{v['id']}">Checkout</button>
                    <button class="action-btn reset-btn" name="reset_{v['id']}">Reset</button>
                </form>
            </td>
        </tr>
        """, unsafe_allow_html=True)

        # Action handlers
        if f"checkout_{v['id']}" in st.query_params:
            mark_checkout(v["id"])
            st.rerun()

        if f"reset_{v['id']}" in st.query_params:
            reset_visitor(v["id"])
            st.rerun()

    st.markdown("</table></div>", unsafe_allow_html=True)


# EXPORT FOR ROUTER
def render_dashboard():
    return render_visitor_dashboard()


# Manual Test
if __name__ == "__main__":
    st.session_state["admin_logged_in"] = True
    st.session_state["admin_name"] = "Test Admin"
    st.session_state["company_id"] = 1
    render_visitor_dashboard()
