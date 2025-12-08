import streamlit as st
import boto3
import json
import mysql.connector
import pandas as pd
from datetime import datetime


# =========================================
# AWS CONFIG
# =========================================
AWS_REGION = "ap-south-1"
AWS_SECRET = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


@st.cache_resource
def get_credentials():
    """Fetch MySQL credentials from AWS Secrets Manager"""
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    secret = client.get_secret_value(SecretId=AWS_SECRET)
    return json.loads(secret["SecretString"])


@st.cache_resource
def get_conn():
    """Establish MySQL connection"""
    c = get_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True
    )


# =========================================
# DB HELPERS
# =========================================
def get_company_user(user_id: int):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT name, company
        FROM conference_users
        WHERE id = %s
        LIMIT 1;
    """, (user_id,))
    return cur.fetchone()


def get_company_bookings(company: str):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT b.id,
               u.name AS booked_by,
               u.department,
               b.start_time,
               b.end_time,
               b.purpose
        FROM conference_bookings b
        INNER JOIN conference_users u ON u.id = b.user_id
        WHERE u.company = %s
        ORDER BY b.start_time DESC;
    """, (company,))
    return cur.fetchall()


# =========================================
# PROFESSIONAL UI CSS
# =========================================
def inject_css():
    st.markdown(f"""
    <style>

    /* Remove Streamlit top padding */
    header[data-testid="stHeader"] {{ display:none; }}
    .block-container {{ padding-top:0rem; }}

    /* HEADER */
    .header-box {{
        background:{GRADIENT};
        padding:32px 42px;
        margin:-1rem -1rem 1.5rem -1rem;
        border-radius:22px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 8px 20px rgba(0,0,0,0.2);
    }}

    .welcome-text {{
        font-size:32px;
        font-weight:900;
        color:white;
    }}

    .company-text {{
        font-size:20px;
        font-weight:600;
        margin-top:4px;
        color:white;
        opacity:0.95;
    }}

    .header-logo {{
        height:60px;
        filter:drop-shadow(0px 0px 4px rgba(255,255,255,0.4));
    }}

    /* ACTION BAR */
    .action-row {{
        display:flex;
        justify-content:space-between;
        margin-bottom:22px;
        margin-top:-10px;
    }}

    .btn-primary {{
        background:{GRADIENT};
        padding:12px 28px;
        border:none;
        border-radius:10px;
        color:white;
        font-weight:700;
        font-size:16px;
        cursor:pointer;
        width:250px;
        box-shadow:0 4px 10px rgba(80,48,157,0.35);
    }}

    .btn-primary:hover {{
        transform:scale(1.02);
    }}

    .btn-logout {{
        background:white;
        padding:11px 28px;
        border:2px solid #50309D;
        border-radius:10px;
        color:#50309D;
        font-weight:700;
        font-size:15px;
        cursor:pointer;
        width:130px;
    }}

    .btn-logout:hover {{
        background:#F1E9FF;
    }}

    /* SUMMARY CARDS */
    .summary-card {{
        background:white;
        padding:16px 20px;
        border-radius:14px;
        box-shadow:0 3px 12px rgba(0,0,0,0.07);
        margin-bottom:16px;
    }}

    .summary-title {{
        font-size:14px;
        opacity:0.7;
        margin-bottom:4px;
    }}

    .summary-value {{
        font-size:26px;
        font-weight:800;
        color:#50309D;
    }}

    /* CLEAN TABLE */
    .dataframe caption {{
        caption-side:top;
        text-align:left;
        font-size:18px;
        font-weight:600;
        margin-bottom:8px;
    }}

    </style>
    """, unsafe_allow_html=True)


# =========================================
# PAGE RENDERING
# =========================================
def render_dashboard():

    inject_css()

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("Unauthorized. Please login.")
        st.stop()

    # Fetch user/company info
    info = get_company_user(user_id)
    company = info["company"]
    user_name = info["name"]

    # Fetch company bookings
    bookings = get_company_bookings(company)

    # ============================= HEADER UI
    st.markdown(f"""
    <div class="header-box">
        <div>
            <div class="welcome-text">Welcome</div>
            <div class="company-text">{company}</div>
        </div>

        <img class="header-logo" src="{LOGO_URL}">
    </div>
    """, unsafe_allow_html=True)

    # ============================= ACTION BAR
    st.markdown("<div class='action-row'>", unsafe_allow_html=True)

    colA, colB = st.columns([1, 1])

    with colA:
        if st.button("New Booking", use_container_width=True):
            st.session_state["current_page"] = "conference_bookings"
            st.rerun()

    with colB:
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.session_state["current_page"] = "conference_login"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # ============================= DASHBOARD CONTENT
    left, right = st.columns([2, 1])

    # ---- BOOKINGS TABLE
    with left:
        st.subheader("Booking List")

        if not bookings:
            st.info("No bookings found.")
        else:
            df = pd.DataFrame(bookings)

            df["Date"] = pd.to_datetime(df["start_time"]).dt.date
            df["Time"] = (
                pd.to_datetime(df["start_time"]).dt.strftime("%I:%M %p")
                + " - "
                + pd.to_datetime(df["end_time"]).dt.strftime("%I:%M %p")
            )

            df = df[["booked_by", "department", "Date", "Time", "purpose"]]
            df.index = df.index + 1

            st.dataframe(df, use_container_width=True, height=480)

    # ---- SUMMARY PANEL
    with right:
        st.subheader("Summary")

        # summary card: today
        today = datetime.today().date()
        today_count = sum(1 for b in bookings if b["start_time"].date() == today)

        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-title">Today's Bookings</div>
            <div class="summary-value">{today_count}</div>
        </div>
        """, unsafe_allow_html=True)

        # summary card: total
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-title">Total Bookings</div>
            <div class="summary-value">{len(bookings)}</div>
        </div>
        """, unsafe_allow_html=True)

        # department breakdown
        st.subheader("By Department")

        dept_map = {}
        for b in bookings:
            dept_map[b["department"]] = dept_map.get(b["department"], 0) + 1

        for dept, count in dept_map.items():
            st.markdown(f"""
            <div class="summary-card">
                <div class="summary-title">{dept}</div>
                <div class="summary-value">{count}</div>
            </div>
            """, unsafe_allow_html=True)
