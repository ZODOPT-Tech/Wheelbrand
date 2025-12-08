import streamlit as st
import boto3
import json
import mysql.connector
import pandas as pd
from datetime import datetime


# =========================
# AWS CONFIG
# =========================
AWS_REGION = "ap-south-1"
AWS_SECRET = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"


@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    data = client.get_secret_value(SecretId=AWS_SECRET)
    return json.loads(data["SecretString"])


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


# =========================
# DB HELPERS
# =========================
def get_company_user(user_id):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT name, company
        FROM conference_users
        WHERE id = %s
        LIMIT 1;
    """, (user_id,))
    return cur.fetchone()


def get_company_bookings(company):
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


# =========================
# CSS
# =========================
def inject_css():
    st.markdown("""
    <style>
    header[data-testid="stHeader"] {display:none;}
    .block-container {padding-top:0rem;}

    .header-box {
        background:linear-gradient(90deg,#50309D,#7A42FF);
        padding:26px 36px;
        margin:-1rem -1rem 1.6rem -1rem;
        border-radius:22px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 6px 18px rgba(0,0,0,0.2);
    }

    .header-left {display:flex;flex-direction:column;}
    .welcome-text {
        font-size:32px;
        font-weight:900;
        color:white;
        margin-bottom:4px;
    }
    .company-text {
        font-size:20px;
        font-weight:600;
        color:white;
        opacity:0.95;
    }
    .header-logo {height:58px;}

    /* Buttons */
    .btn-purple {
        background:linear-gradient(90deg,#50309D,#7A42FF);
        padding:11px 28px;
        border:none;
        border-radius:9px;
        color:white;
        font-size:16px;
        font-weight:700;
        cursor:pointer;
        width:220px;
    }

    .btn-outline {
        background:white;
        padding:11px 28px;
        border:2px solid #50309D;
        border-radius:9px;
        color:#50309D;
        font-size:15px;
        font-weight:700;
        cursor:pointer;
        width:120px;
    }
    .btn-outline:hover {
        background:#F2EAFF;
    }
    </style>
    """, unsafe_allow_html=True)


# =========================
# PAGE RENDERING
# =========================
def render_dashboard():

    inject_css()

    # Check login
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("Unauthorized. Please login.")
        st.stop()

    # Load user details
    info = get_company_user(user_id)
    company = info["company"]
    user_name = info["name"]

    # Load bookings
    bookings = get_company_bookings(company)

    # ==================== HEADER
    st.markdown(f"""
    <div class="header-box">
        <div class="header-left">
            <div class="welcome-text">Welcome</div>
            <div class="company-text">{company}</div>
        </div>
        <img class="header-logo"
             src="https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"/>
    </div>
    """, unsafe_allow_html=True)

    # ==================== ACTION BAR (No hidden buttons)
    action_col1, action_col2 = st.columns([1, 1])

    with action_col1:
        if st.button("New Booking", use_container_width=True):
            st.session_state["current_page"] = "conference_bookings"
            st.rerun()

    with action_col2:
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.session_state["current_page"] = "conference_login"
            st.rerun()

    st.write("")

    # ==================== DASHBOARD
    left, right = st.columns([2, 1])

    # ---- BOOKING LIST
    with left:
        st.subheader("Booking List")
        if not bookings:
            st.info("No bookings found.")
        else:
            df = pd.DataFrame(bookings)
            df["Date"] = pd.to_datetime(df["start_time"]).dt.date
            df["Time"] = (
                    pd.to_datetime(df["start_time"]).dt.strftime("%I:%M %p")
                    + " - " +
                    pd.to_datetime(df["end_time"]).dt.strftime("%I:%M %p")
            )

            df = df[["booked_by", "department", "Date", "Time", "purpose"]]
            df.index = df.index + 1

            st.dataframe(df, use_container_width=True, height=460)

    # ---- SUMMARY RIGHT
    with right:
        st.subheader("Summary")

        today = datetime.today().date()
        today_count = sum(1 for b in bookings if b["start_time"].date() == today)

        st.metric("Today's Bookings", today_count)
        st.metric("Total Bookings", len(bookings))

        st.write("---")
        st.subheader("By Department")

        dept_map = {}
        for b in bookings:
            dept_map[b["department"]] = dept_map.get(b["department"], 0) + 1

        for dept, count in dept_map.items():
            st.metric(dept, count)
