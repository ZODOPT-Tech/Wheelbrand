import streamlit as st
import boto3
import json
import mysql.connector
from datetime import datetime
import pandas as pd

# ------------------------------------------------------
# AWS DB CONFIG
# ------------------------------------------------------
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    secret = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(secret["SecretString"])

@st.cache_resource
def get_conn():
    creds = get_credentials()
    return mysql.connector.connect(
        host=creds["DB_HOST"],
        user=creds["DB_USER"],
        password=creds["DB_PASSWORD"],
        database=creds["DB_NAME"],
        autocommit=True,
    )


# ------------------------------------------------------
# UI CONFIG
# ------------------------------------------------------
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"


def set_dashboard_css():
    st.markdown("""
    <style>
    header[data-testid="stHeader"]{display:none;}
    .block-container{padding-top:0rem;}

    .header-box {
        background:linear-gradient(90deg,#50309D,#7A42FF);
        padding:24px 32px;
        margin:-1rem -1rem 1.2rem -1rem;
        border-radius:18px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 6px 16px rgba(0,0,0,0.18);
    }

    .header-left{display:flex;flex-direction:column;}
    .header-title{font-size:28px;font-weight:800;color:white;}
    .header-sub{font-size:17px;font-weight:500;color:white;opacity:0.85;}

    .header-right{
        display:flex;
        align-items:center;
    }
    .header-logo{height:50px;}

    .action-bar{
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin-bottom:1rem;
    }

    .stButton>button {
        background: linear-gradient(90deg,#50309D,#7A42FF) !important;
        color:white !important;
        border:none !important;
        border-radius:8px !important;
        font-weight:600 !important;
        padding:10px 20px !important;
        font-size:15px !important;
    }

    .logout-btn {
        background:none;
        border:none;
        cursor:pointer;
    }
    .logout-icon {
        width:32px;
        transition:0.25s;
    }
    .logout-icon:hover {filter:brightness(200%);}
    </style>
    """, unsafe_allow_html=True)


# ------------------------------------------------------
# DB HELPERS
# ------------------------------------------------------
def get_user_details(user_id):
    conn = get_conn()
    c = conn.cursor(dictionary=True)
    c.execute("""
        SELECT id, name, company
        FROM conference_users
        WHERE id=%s AND is_active=1
    """, (user_id,))
    return c.fetchone()


def load_company_bookings(company):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            b.id,
            b.booking_date,
            b.start_time,
            b.end_time,
            b.purpose,
            u.name AS employee_name,
            u.department
        FROM conference_bookings b
        JOIN conference_users u ON u.id = b.user_id
        WHERE u.company = %s
        ORDER BY b.start_time DESC
    """, (company,))
    return cursor.fetchall()


# ------------------------------------------------------
# HEADER
# ------------------------------------------------------
def render_header(user):
    st.markdown(f"""
    <div class="header-box">
        <div class="header-left">
            <div class="header-title">Welcome, {user['company']}</div>
            <div class="header-sub">{user['name']}</div>
        </div>

        <div class="header-right">
            <img class="header-logo" src="{LOGO_URL}"/>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------
def render_dashboard():

    if "user_id" not in st.session_state:
        st.session_state["current_page"] = "conference_login"
        st.rerun()

    set_dashboard_css()

    # Get user info from DB
    user = get_user_details(st.session_state["user_id"])
    render_header(user)

    # Load bookings for this company
    bookings = load_company_bookings(user["company"])

    # --- Action Row (same line)
    st.markdown('<div class="action-bar">', unsafe_allow_html=True)
    col1, col2 = st.columns([8,1])

    with col1:
        if st.button("New Booking"):
            st.session_state["current_page"] = "conference_bookings"
            st.rerun()

    with col2:
        if st.button("Logout", key="logout_btn"):
            st.session_state.clear()
            st.session_state["current_page"] = "conference_login"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


    # --- Layout
    col_left, col_right = st.columns([2,1])

    # LEFT — Bookings Table
    with col_left:
        st.write("### Booking List")

        if not bookings:
            st.info("No bookings found.")
        else:
            # Convert to dataframe
            df = pd.DataFrame(bookings)

            df["Date"] = pd.to_datetime(df["start_time"]).dt.date
            df["Time"] = (
                pd.to_datetime(df["start_time"]).dt.strftime("%I:%M %p")
                + " — " +
                pd.to_datetime(df["end_time"]).dt.strftime("%I:%M %p")
            )

            # Only required columns
            df = df[["employee_name","department","Date","Time","purpose"]]

            # Rename headings
            df.columns = ["Booked By","Department","Date","Time","Purpose"]

            # Add Index starting from 1
            df.index = df.index + 1
            df.index.name = "S.No"

            st.dataframe(df, use_container_width=True, height=430)


    # RIGHT — Summary Metrics
    with col_right:
        st.write("### Summary")

        today = datetime.today().date()
        today_count = sum(1 for b in bookings if b["booking_date"] == today)
        total_count = len(bookings)

        st.metric("Today's Bookings", today_count)
        st.metric("Total Bookings", total_count)

        st.markdown("---")
        st.write("#### By Department")

        dept_count = {}
        for b in bookings:
            d = b["department"]
            dept_count[d] = dept_count.get(d, 0) + 1

        for d,c in dept_count.items():
            st.metric(d, c)

        st.markdown("---")
        st.write("#### By Purpose")

        purpose_count = {}
        for b in bookings:
            p = b["purpose"]
            purpose_count[p] = purpose_count.get(p, 0) + 1

        for p,c in purpose_count.items():
            st.metric(p, c)
