import streamlit as st
import boto3
import json
import mysql.connector
import pandas as pd
from datetime import datetime


# ==============================
# AWS + DB CONFIG
# ==============================
AWS_REGION = "ap-south-1"
AWS_SECRET = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    result = client.get_secret_value(SecretId=AWS_SECRET)
    return json.loads(result["SecretString"])


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


# ==============================
# DB HELPERS
# ==============================
def get_company_user(user_id):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT name, company FROM conference_users WHERE id=%s LIMIT 1;",
        (user_id,)
    )
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
        JOIN conference_users u ON u.id=b.user_id
        WHERE u.company=%s
        ORDER BY b.start_time DESC;
    """, (company,))
    return cur.fetchall()


# ==============================
# UI CSS
# ==============================
def inject_css():
    st.markdown(f"""
    <style>

    header[data-testid="stHeader"] {{display:none;}}
    .block-container {{padding-top:0;}}

    .header-box {{
        background:{GRADIENT};
        margin:-1rem -1rem 1.5rem -1rem;
        border-radius:20px;
        padding:28px 40px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 6px 20px rgba(0,0,0,0.18);
    }}

    .welcome {{
        font-size:32px;
        font-weight:900;
        color:white;
        margin-bottom:5px;
    }}
    .company {{
        font-size:20px;
        font-weight:600;
        color:white;
        opacity:0.9;
    }}
    .header-logo {{
        height:60px;
    }}

    .btn-primary {{
        background:{GRADIENT};
        color:white;
        font-weight:700;
        border:none;
        padding:10px 26px;
        border-radius:9px;
        width:230px;
        font-size:16px;
    }}
    .btn-outline {{
        background:white;
        font-weight:700;
        color:#50309D;
        border:2px solid #50309D;
        padding:10px 26px;
        border-radius:9px;
        width:120px;
        font-size:15px;
    }}
    .btn-outline:hover {{
        background:#EFE7FF;
    }}

    .summary-card {{
        background:white;
        padding:16px 22px;
        border-radius:14px;
        box-shadow:0 3px 12px rgba(0,0,0,0.1);
        margin-bottom:16px;
    }}
    .summary-title {{
        font-size:14px;
        opacity:0.7;
    }}
    .summary-value {{
        font-size:26px;
        font-weight:800;
        color:#50309D;
    }}

    </style>
    """, unsafe_allow_html=True)


# ==============================
# DASHBOARD RENDER
# ==============================
def render_dashboard():

    inject_css()

    # Auth check
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("Unauthorized. Login again.")
        st.stop()

    # Load user data
    user = get_company_user(user_id)
    company = user["company"]

    # Load bookings
    bookings = get_company_bookings(company)

    # ---------------- HEADER
    st.markdown(
        f"""
        <div class="header-box">
            <div>
                <div class="welcome">Welcome</div>
                <div class="company">{company}</div>
            </div>
            <img class="header-logo" src="{LOGO_URL}">
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------- ACTION BAR (same line)
    left_action, right_action = st.columns([1, 1])

    with left_action:
        if st.button("New Booking", use_container_width=True):
            st.session_state["current_page"] = "conference_bookings"
            st.rerun()

    with right_action:
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.session_state["current_page"] = "conference_login"
            st.rerun()

    # spacing
    st.write("")

    # ---------------- DASHBOARD BODY
    col_left, col_right = st.columns([2, 1])

    # ---- SUMMARY (RIGHT FIRST as per request)
    with col_right:
        st.subheader("Summary")

        today = datetime.today().date()
        today_count = sum(1 for b in bookings if b["start_time"].date() == today)

        st.markdown(
            f"""
            <div class="summary-card">
                <div class="summary-title">Today's Bookings</div>
                <div class="summary-value">{today_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="summary-card">
                <div class="summary-title">Total Bookings</div>
                <div class="summary-value">{len(bookings)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("By Department")
        dept_count = {}
        for b in bookings:
            dept_count[b["department"]] = dept_count.get(b["department"], 0) + 1

        for dept, count in dept_count.items():
            st.markdown(
                f"""
                <div class="summary-card">
                    <div class="summary-title">{dept}</div>
                    <div class="summary-value">{count}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ---- BOOKING LIST
    with col_left:
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
            df.index = df.index + 1  # start at 1

            st.dataframe(df, use_container_width=True, height=480)
