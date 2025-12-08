import streamlit as st
import boto3
import json
import mysql.connector
import pandas as pd
from datetime import datetime


# ================================
# AWS + DB CONFIG
# ================================
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    data = client.get_secret_value(SecretId=AWS_SECRET_NAME)
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


# ================================
# DB QUERIES
# ================================
def get_company_and_name(user_id: int):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT company, name 
        FROM conference_users
        WHERE id = %s
        LIMIT 1;
    """, (user_id,))
    return cur.fetchone()


def get_company_bookings(company_name: str):
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
    """, (company_name,))
    return cur.fetchall()


# ================================
# CSS
# ================================
def inject_css():
    st.markdown(f"""
    <style>

    header[data-testid="stHeader"] {{
        display:none;
    }}

    .block-container {{
        padding-top:0;
    }}

    /* HEADER */
    .header-box {{
        background:{GRADIENT};
        padding:28px 36px;
        margin:-1rem -1rem 1.2rem -1rem;
        border-radius:22px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 6px 18px rgba(0,0,0,0.2);
    }}

    .header-left {{
        display:flex;
        flex-direction:column;
    }}

    .welcome-text {{
        font-size:32px;
        font-weight:900;
        color:white;
        margin-bottom:3px;
    }}

    .company-text {{
        font-size:20px;
        font-weight:600;
        color:white;
        opacity:0.95;
    }}

    .header-logo {{
        height:56px;
    }}

    /* ACTION BAR */
    .action-row {{
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin:10px 0 25px 0;
    }}

    .btn-primary {{
        background:{GRADIENT};
        padding:10px 28px;
        border:none;
        border-radius:9px;
        font-size:16px;
        font-weight:700;
        color:white;
        cursor:pointer;
        width:240px;
        text-align:center;
    }}

    .btn-secondary {{
        background:white;
        padding:10px 24px;
        border:2px solid #50309D;
        border-radius:9px;
        font-size:15px;
        font-weight:600;
        color:#50309D;
        cursor:pointer;
        width:120px;
        text-align:center;
    }}

    .btn-primary:hover {{
        opacity:0.92;
    }}
    .btn-secondary:hover {{
        background:#f2eaff;
    }}

    </style>
    """, unsafe_allow_html=True)


# ================================
# MAIN RENDER
# ================================
def render_dashboard():

    inject_css()

    user_id = st.session_state.get("user_id", None)
    if not user_id:
        st.error("Unauthorized access.")
        st.stop()

    # ---- FETCH user info
    info = get_company_and_name(user_id)
    if not info:
        st.error("User profile not found.")
        st.stop()

    company = info["company"]
    user_name = info["name"]

    # ---- FETCH bookings
    bookings = get_company_bookings(company)

    # ========================= HEADER
    st.markdown(f"""
    <div class="header-box">
        <div class="header-left">
            <div class="welcome-text">Welcome</div>
            <div class="company-text">{company}</div>
        </div>
        <img class="header-logo" src="{LOGO_URL}">
    </div>
    """, unsafe_allow_html=True)

    # ========================= ACTION BAR
    col1, col2 = st.columns([1, 1])

    with col1:
        # hidden trigger button for streamlit
        if st.button("new_booking_hidden", key="new_booking", help="", args=None):
            st.session_state["current_page"] = "conference_bookings"
            st.rerun()

        st.markdown("""
            <div class="action-row">
                <button class="btn-primary" onclick="document.getElementById('new_booking').click();">
                    New Booking
                </button>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        if st.button("logout_hidden", key="logout", help="", args=None):
            st.session_state.clear()
            st.session_state["current_page"] = "conference_login"
            st.rerun()

        st.markdown("""
            <div class="action-row" style="justify-content:flex-end;">
                <button class="btn-secondary" onclick="document.getElementById('logout').click();">
                    Logout
                </button>
            </div>
        """, unsafe_allow_html=True)

    # ========================= DASHBOARD CONTENT
    left, right = st.columns([2, 1])

    # ---- BOOKING TABLE
    with left:
        st.subheader("Booking List")

        if not bookings:
            st.info("No active bookings found.")
        else:
            df = pd.DataFrame(bookings)

            df["Date"] = pd.to_datetime(df["start_time"]).dt.date
            df["Time"] = (
                pd.to_datetime(df["start_time"]).dt.strftime("%I:%M %p") + " - " +
                pd.to_datetime(df["end_time"]).dt.strftime("%I:%M %p")
            )

            df = df[["booked_by", "department", "Date", "Time", "purpose"]]
            df.index = df.index + 1  # start from 1

            st.dataframe(df,
                         use_container_width=True,
                         height=450)

    # ---- SUMMARY
    with right:
        st.subheader("Summary")

        today = datetime.today().date()
        today_count = sum(1 for b in bookings if b["start_time"].date() == today)

        st.metric("Today", today_count)
        st.metric("Total", len(bookings))

        st.write("---")
        st.subheader("By Department")

        dept_map = {}
        for b in bookings:
            dept_map[b["department"]] = dept_map.get(b["department"], 0) + 1

        for d, c in dept_map.items():
            st.metric(d, c)
