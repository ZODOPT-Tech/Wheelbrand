import streamlit as st
import boto3
import json
import mysql.connector
import pandas as pd
from datetime import datetime


# ===========================================================
# AWS + DB CONFIG
# ===========================================================

AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    secret = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(secret["SecretString"])


@st.cache_resource
def get_connection():
    creds = get_credentials()
    return mysql.connector.connect(
        host=creds["DB_HOST"],
        user=creds["DB_USER"],
        password=creds["DB_PASSWORD"],
        database=creds["DB_NAME"],
        autocommit=True
    )


# ===========================================================
# CSS
# ===========================================================
def inject_css():
    st.markdown("""
    <style>
        header[data-testid="stHeader"] {display: none;}
        .block-container {padding-top: 0rem;}

        .header-box {
            background: linear-gradient(90deg,#50309D,#7A42FF);
            padding: 26px 36px;
            margin: -1rem -1rem 1rem -1rem;
            border-radius: 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow:0 5px 16px rgba(0,0,0,0.18);
        }

        .header-left {display:flex; flex-direction:column;}

        .welcome-text {
            font-size: 34px;
            font-weight: 800;
            color: white;
        }
        .username-text {
            font-size: 17px;
            margin-top: 4px;
            font-weight: 500;
            color: white;
        }

        .header-actions {display:flex; align-items:center; gap: 14px;}

        .header-logo {
            height: 48px;
        }

        .logout-btn-icon {
            width: 30px;
            cursor:pointer;
            transition:0.25s;
        }
        .logout-btn-icon:hover {filter: brightness(2);}

        .btn-purple {
            background: linear-gradient(90deg,#50309D,#7A42FF)!important;
            color: white!important;
            font-weight:600;
            padding:9px 22px!important;
            border-radius:8px!important;
            border: none!important;
            font-size:15px!important;
        }
    </style>
    """, unsafe_allow_html=True)


# ===========================================================
# HEADER
# ===========================================================
def render_header():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM conference_users WHERE id=%s", (st.session_state["user_id"],))
    user = cursor.fetchone()

    company = user.get("company","")
    username = user.get("name","")

    st.markdown(f"""
        <div class="header-box">
            <div class="header-left">
                <div class="welcome-text">Welcome, {company}</div>
                <div class="username-text">{username}</div>
            </div>

            <div class="header-actions">
                <button class="btn-purple" onclick="document.getElementById('new_booking').click();">
                    New Booking
                </button>

                <img class="header-logo" src="https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"/>

                <img class="logout-btn-icon"
                     src="https://cdn-icons-png.flaticon.com/512/1828/1828490.png"
                     onclick="document.getElementById('logout_btn').click();"/>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # hidden buttons
    if st.button("New Booking", key="new_booking", help="", type="primary"):
        st.session_state["current_page"] = "conference_bookings"
        st.rerun()

    if st.button("logout", key="logout_btn", help="", type="primary"):
        st.session_state.clear()
        st.session_state["current_page"] = "conference_login"
        st.rerun()


# ===========================================================
# FETCH COMPANY BOOKINGS
# ===========================================================
def load_company_bookings():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.*, u.name AS booked_by, u.department, u.company
        FROM conference_bookings b
        JOIN conference_users u ON u.id = b.user_id
        WHERE u.company = (SELECT company FROM conference_users WHERE id=%s)
        ORDER BY b.start_time DESC
    """,(st.session_state["user_id"],))

    return cursor.fetchall()


# ===========================================================
# DASHBOARD PAGE
# ===========================================================
def render_dashboard():

    inject_css()
    render_header()

    bookings = load_company_bookings()

    st.markdown("<h3 style='font-weight:700;margin-bottom:18px;'>Booking List</h3>", unsafe_allow_html=True)

    col1, col2 = st.columns([2,1])

    with col1:
        if not bookings:
            st.info("No bookings found.")
        else:
            df = pd.DataFrame(bookings)

            df["Date"] = pd.to_datetime(df["start_time"]).dt.date
            df["Time"] = (
                pd.to_datetime(df["start_time"]).dt.strftime("%I:%M %p")
                + " — " +
                pd.to_datetime(df["end_time"]).dt.strftime("%I:%M %p")
            )

            df = df[["booked_by","department","Date","Time","purpose"]]
            df.index = df.index + 1  # start S.No from 1
            df.index.name = "S.No"

            st.dataframe(df, use_container_width=True)


    with col2:
        st.markdown("<h3 style='font-weight:700;margin-bottom:18px;'>Summary</h3>", unsafe_allow_html=True)

        today = datetime.today().date()
        today_count = sum(1 for b in bookings if b["booking_date"] == today)

        st.metric("Today's Bookings", today_count)
        st.metric("Total Bookings", len(bookings))

        st.write("---")

        dept_count = {}
        for b in bookings:
            d = b["department"]
            dept_count[d] = dept_count.get(d,0)+1

        st.markdown("**By Department**")
        for d,c in dept_count.items():
            st.metric(d, c)


# ===========================================================
# ENTRY POINT
# ===========================================================
def render_conference_dashboard():
    if "user_id" not in st.session_state:
        st.session_state["current_page"] = "conference_login"
        st.rerun()
    render_dashboard()
