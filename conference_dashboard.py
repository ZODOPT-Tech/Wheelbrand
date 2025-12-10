
import streamlit as st
import boto3
import json
import mysql.connector
import pandas as pd
from datetime import datetime


# ===================================
# CONFIG
# ===================================
AWS_REGION = "ap-south-1"
AWS_SECRET = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


# ===================================
# DB + SECRETS
# ===================================
@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    result = client.get_secret_value(SecretId=AWS_SECRET)
    return json.loads(result["SecretString"])


@st.cache_resource
def get_conn():
    """Persistent DB connection"""
    c = get_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True
    )


def get_company_user(user_id: int):
    """No caching → reflects live changes"""
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT name, company FROM conference_users WHERE id=%s LIMIT 1",
        (user_id,)
    )
    return cur.fetchone()


def get_company_bookings(company: str):
    """No caching → reflects live bookings"""
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


# ===================================
# CUSTOM CSS
# ===================================
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


# ===================================
# MAIN DASHBOARD
# ===================================
def render_dashboard():

    inject_css()

    # -----------------------------------
    # AUTH CHECK
    # -----------------------------------
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("Unauthorized. Login again.")
        st.stop()

    # USER INFO
    user = get_company_user(user_id)
    company = user["company"]

    # -----------------------------------
    # LIVE BOOKINGS → ONLY TODAY
    # -----------------------------------
    all_bookings = get_company_bookings(company)
    today = datetime.today().date()

    todays_bookings = [
        b for b in all_bookings
        if b["start_time"].date() == today
    ]

    # -----------------------------------
    # DEPARTMENT COUNT
    # -----------------------------------
    dept_count = {}
    for b in todays_bookings:
        dept = b["department"]
        dept_count[dept] = dept_count.get(dept, 0) + 1

    # -----------------------------------
    # HEADER
    # -----------------------------------
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

    # -----------------------------------
    # ACTIONS
    # -----------------------------------
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

    st.write("")

    # -----------------------------------
    # BODY
    # -----------------------------------
    col_left, col_right = st.columns([2, 1])

    # SUMMARY
    with col_right:
        st.subheader("Summary (Today)")

        st.markdown(
            f"""
            <div class="summary-card">
                <div class="summary-title">Today's Bookings</div>
                <div class="summary-value">{len(todays_bookings)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("By Department")

        if not dept_count:
            st.info("No bookings today.")
        else:
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

    # TABLE
    with col_left:
        st.subheader("Today's Booking List")

        if not todays_bookings:
            st.info("No bookings today.")
        else:
            df = pd.DataFrame(todays_bookings)
            df["Date"] = pd.to_datetime(df["start_time"]).dt.date
            df["Time"] = (
                pd.to_datetime(df["start_time"]).dt.strftime("%I:%M %p")
                + " - "
                + pd.to_datetime(df["end_time"]).dt.strftime("%I:%M %p")
            )

            df = df[["booked_by", "department", "Date", "Time", "purpose"]]
            df.index = df.index + 1

            st.dataframe(df, use_container_width=True, height=480)
