import streamlit as st
import mysql.connector
from datetime import datetime
import json
import boto3

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

    .summary-card {{
        background: white;
        padding: 18px 20px;
        border-radius: 12px;
        margin-bottom: 18px;
        text-align: left;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
    }}

    .summary-title {{
        font-size: 15px;
        color: #666;
        font-weight: 600;
        margin-bottom: 4px;
    }}

    .summary-value {{
        font-size: 26px;
        font-weight: 800;
        color: #4B2ECF;
    }}

    .completed {{
        background: #28a745;
        padding: 6px 12px;
        border-radius: 6px;
        color: white;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
    }}

    .checkout-btn button {{
        background: {HEADER_GRADIENT} !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 8px 14px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        border: none !important;
    }}

    .new-btn button {{
        background: {HEADER_GRADIENT} !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 18px !important;
        font-size: 20px !important;
        font-weight: 700 !important;
        width: 100% !important;
    }}
    </style>
    """, unsafe_allow_html=True)


# ======================================================
# HEADER
# ======================================================

def render_header():
    company_name = st.session_state.get("company_name", "Your Company")

    st.markdown(f"""
        <div class="header-box">
            <div class="header-title">Welcome, {company_name}</div>
            <img src="{LOGO_URL}" class="header-logo">
        </div>
    """, unsafe_allow_html=True)


# ======================================================
# FETCH VISITORS — ONLY APPROVED + PASS GENERATED
# ======================================================

def get_visitors(company_id):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT visitor_id, full_name, phone_number, person_to_meet,
               registration_timestamp, checkout_time
        FROM visitors
        WHERE company_id = %s
          AND status = 'approved'
          AND pass_generated = 1
          AND DATE(registration_timestamp) = CURDATE()
        ORDER BY registration_timestamp DESC
    """, (company_id,))
    return cursor.fetchall()


# ======================================================
# DASHBOARD STATS — APPROVED + PASS GENERATED
# ======================================================

def dashboard_stats(company_id):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(*) AS c 
        FROM visitors 
        WHERE company_id=%s 
          AND status='approved'
          AND pass_generated = 1
          AND DATE(registration_timestamp)=CURDATE()
    """, (company_id,))
    visitors_today = cursor.fetchone()['c']

    cursor.execute("""
        SELECT COUNT(*) AS c 
        FROM visitors
        WHERE company_id=%s 
          AND status='approved'
          AND pass_generated = 1
          AND checkout_time IS NULL
          AND DATE(registration_timestamp)=CURDATE()
    """, (company_id,))
    inside_now = cursor.fetchone()['c']

    cursor.execute("""
        SELECT COUNT(*) AS c 
        FROM visitors
        WHERE company_id=%s 
          AND status='approved'
          AND pass_generated = 1
          AND DATE(checkout_time)=CURDATE()
    """, (company_id,))
    checked_out_today = cursor.fetchone()['c']

    return visitors_today, inside_now, checked_out_today, visitors_today


# ======================================================
# MARK CHECKOUT
# ======================================================

def mark_checkout(visitor_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE visitors SET checkout_time=%s WHERE visitor_id=%s",
        (datetime.now(), visitor_id)
    )


# ======================================================
# MAIN DASHBOARD
# ======================================================

def render_visitor_dashboard():

    if "admin_logged_in" not in st.session_state or not st.session_state["admin_logged_in"]:
        st.error("Access Denied")
        st.stop()

    load_css()
    render_header()

    company_id = st.session_state["company_id"]

    visitors_today, inside_now, checked_out_today, total_visitors = dashboard_stats(company_id)

    left, right = st.columns([4, 1.4])

    # ================= RIGHT SUMMARY =================
    with right:
        st.markdown("### 📊 Summary")

        st.markdown(f"""
            <div class="summary-card">
                <div class="summary-title">Visitors Today</div>
                <div class="summary-value">{visitors_today}</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="summary-card">
                <div class="summary-title">Currently Inside</div>
                <div class="summary-value">{inside_now}</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="summary-card">
                <div class="summary-title">Checked Out Today</div>
                <div class="summary-value">{checked_out_today}</div>
            </div>
        """, unsafe_allow_html=True)


    # ================= LEFT LIST =================
    with left:

        st.markdown("<div class='new-btn'>", unsafe_allow_html=True)
        if st.button("NEW VISITOR REGISTRATION"):
            st.session_state["current_page"] = "visitor_details"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("## Visitor List")

        visitors = get_visitors(company_id)

        if not visitors:
            st.info("No approved visitors today.")
            return

        # Header
        header = st.columns([3, 2, 2, 3, 2, 2])
        header[0].markdown("### Name")
        header[1].markdown("### Phone")
        header[2].markdown("### Meeting")
        header[3].markdown("### Visited")
        header[4].markdown("### Checkout")
        header[5].markdown("### Action")

        st.markdown("---")

        # Rows
        for v in visitors:
            vid = v["visitor_id"]
            checkout_val = v["checkout_time"].strftime("%d-%m-%Y %H:%M") if v["checkout_time"] else "—"

            row = st.columns([3, 2, 2, 3, 2, 2])

            row[0].write(v["full_name"])
            row[1].write(v["phone_number"])
            row[2].write(v["person_to_meet"])
            row[3].write(v["registration_timestamp"].strftime("%d-%m-%Y %H:%M"))
            row[4].write(checkout_val)

            with row[5]:
                if not v["checkout_time"]:
                    if st.button("Checkout", key=f"checkout_{vid}"):
                        mark_checkout(vid)
                        st.rerun()
                else:
                    st.markdown("<div class='completed'>Completed</div>", unsafe_allow_html=True)


# EXPORT FOR ROUTER
def render_dashboard():
    return render_visitor_dashboard()
