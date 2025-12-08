import streamlit as st
import boto3
import json
import mysql.connector
from datetime import datetime
import pandas as pd


# -------------------------------------------------------
# AWS & DB CONFIG
# -------------------------------------------------------
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
        autocommit=True
    )


# -------------------------------------------------------
# UI CONFIG
# -------------------------------------------------------
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


# -------------------------------------------------------
# CUSTOM GLOBAL CSS
# -------------------------------------------------------
def set_global_css():
    st.markdown("""
    <style>
    header[data-testid="stHeader"] {display:none!important;}
    .block-container {padding-top:0;}

    .header-box {
        background:linear-gradient(90deg,#50309D,#7A42FF);
        padding:24px 36px;
        margin:-1rem -1rem 2rem -1rem;
        border-radius:20px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 6px 18px rgba(0,0,0,0.18);
    }

    .header-left {display:flex;flex-direction:column;}

    .header-title {
        font-size:30px;
        font-weight:800;
        color:white;
        margin-bottom:4px;
    }

    .header-sub {
        font-size:17px;
        font-weight:500;
        color:white;
        opacity:0.88;
    }

    .header-right {
        display:flex;
        align-items:center;
        gap:18px;
    }

    .header-logo {height:48px;}

    .logout-icon {
        width:30px;
        cursor:pointer;
        transition:0.3s;
    }
    .logout-icon:hover {filter:brightness(200%);}
    
    </style>
    """, unsafe_allow_html=True)


# -------------------------------------------------------
# HEADER COMPONENT
# -------------------------------------------------------
def render_header():

    username = st.session_state.get("user_name", "")
    company = st.session_state.get("company", "")

    st.markdown(f"""
        <div class="header-box">
            <div class="header-left">
                <div class="header-title">Welcome, {company}</div>
                <div class="header-sub">{username}</div>
            </div>

            <div class="header-right">
                <img class="header-logo" src="{LOGO_URL}"/>

                <img class="logout-icon"
                     src="https://cdn-icons-png.flaticon.com/512/1828/1828490.png"
                     onclick="document.getElementById('hidden_logout').click();"/>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # hidden logout trigger
    col1, col2, col3 = st.columns([9,1,1])
    with col2:
        logout_trigger = st.button("logout", key="hidden_logout", label_visibility="hidden")

    if logout_trigger:
        st.session_state.clear()
        st.session_state["current_page"] = "conference_login"
        st.rerun()


# -------------------------------------------------------
# FETCH BOOKINGS
# -------------------------------------------------------
def load_company_bookings(company):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.*, u.name AS employee_name, u.department
        FROM conference_bookings b
        JOIN conference_users u ON u.id = b.user_id
        WHERE u.company = %s
        ORDER BY b.start_time DESC
    """, (company,))
    return cursor.fetchall()


# -------------------------------------------------------
# DASHBOARD PAGE
# -------------------------------------------------------
def render_dashboard():

    set_global_css()
    render_header()

    company = st.session_state.get("company")
    bookings = load_company_bookings(company)

    # New booking button
    if st.button("➕ New Booking", use_container_width=True):
        st.session_state['current_page'] = "conference_bookings"
        st.rerun()

    st.write("")

    col_left, col_right = st.columns([2,1])

    # Left : Bookings Table
    with col_left:
        st.subheader("📅 Booking List")

        if not bookings:
            st.info("No bookings found yet.")
        else:
            df = pd.DataFrame(bookings)
            df["Date"] = pd.to_datetime(df["start_time"]).dt.date
            df["Time"] = (
                pd.to_datetime(df["start_time"]).dt.strftime("%I:%M %p")
                + " - " +
                pd.to_datetime(df["end_time"]).dt.strftime("%I:%M %p")
            )

            df = df[["employee_name", "department", "Date", "Time", "purpose"]]
            df.columns = ["Booked By", "Department", "Date", "Time", "Purpose"]

            st.dataframe(df, use_container_width=True, height=430)


    # Right : Metrics
    with col_right:
        st.subheader("📊 Summary")

        today = datetime.today().date()

        today_count = len([b for b in bookings if b.get("booking_date") == today])
        all_count = len(bookings)

        st.metric("Today's Bookings", today_count)
        st.metric("Total Bookings", all_count)

        # department metric
        st.markdown("---")
        st.write("#### By Department")

        dept = {}
        for b in bookings:
            d = b["department"]
            dept[d] = dept.get(d, 0) + 1

        for d, c in dept.items():
            st.metric(d, c)

        # purpose
        st.markdown("---")
        st.write("#### By Purpose")

        purpose = {}
        for b in bookings:
            p = b["purpose"]
            purpose[p] = purpose.get(p, 0) + 1

        for p, c in purpose.items():
            st.metric(p, c)
