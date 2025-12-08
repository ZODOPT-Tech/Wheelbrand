import streamlit as st
import boto3
import json
import mysql.connector
import pandas as pd
from datetime import datetime


# =====================================================
# AWS Secrets & Database Connection
# =====================================================
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"


@st.cache_resource
def get_db_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    secret_data = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(secret_data["SecretString"])


@st.cache_resource
def db_conn():
    creds = get_db_credentials()
    return mysql.connector.connect(
        host=creds["DB_HOST"],
        user=creds["DB_USER"],
        password=creds["DB_PASSWORD"],
        database=creds["DB_NAME"],
        autocommit=True
    )


# =====================================================
# Global CSS (Professional Styling)
# =====================================================
def load_css():
    st.markdown("""
    <style>
        header[data-testid="stHeader"] {
            display: none;
        }
        .block-container {
            padding-top: 0px;
        }

        .header-container {
            width: 100%;
            background: linear-gradient(90deg, #50309D, #7A42FF);
            padding: 26px 40px;
            border-radius: 20px;
            margin: -1rem -1rem 1.5rem -1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 6px 18px rgba(0,0,0,0.18);
        }

        .welcome-title {
            font-size: 34px;
            font-weight: 800;
            color: white;
            margin: 0;
        }

        .username {
            font-size: 17px;
            color: white;
            opacity: 0.92;
            margin-top: 4px;
            font-weight: 500;
        }

        .action-buttons {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .btn-primary {
            padding: 8px 22px !important;
            border-radius: 8px !important;
            border: none !important;
            background: linear-gradient(90deg, #50309D, #7A42FF) !important;
            color: white !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            cursor: pointer;
        }

        .logo-img {
            height: 48px;
        }

        .logout-icon {
            width: 30px;
            cursor: pointer;
            transition: 0.22s ease-in-out;
        }
        .logout-icon:hover {
            filter: brightness(2);
            transform: scale(1.08);
        }

    </style>
    """, unsafe_allow_html=True)


# =====================================================
# Header UI
# =====================================================
def render_header():
    conn = db_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name, company FROM conference_users WHERE id=%s",
                   (st.session_state["user_id"],))
    user = cursor.fetchone()

    username = user["name"]
    company = user["company"]

    st.markdown(f"""
        <div class="header-container">
            <div>
                <div class="welcome-title">Welcome, {company}</div>
                <div class="username">{username}</div>
            </div>

            <div class="action-buttons">
                <button class="btn-primary" onclick="document.getElementById('new_booking').click()">
                    New Booking
                </button>

                <img class="logo-img"
                     src="https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"/>

                <img class="logout-icon"
                     src="https://cdn-icons-png.flaticon.com/512/1828/1828490.png"
                     onclick="document.getElementById('logout_click').click()"/>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # hidden button triggers
    if st.button("hidden_new_booking", key="new_booking", help="", type="secondary"):
        st.session_state["current_page"] = "conference_bookings"
        st.rerun()

    if st.button("hidden_logout", key="logout_click", help="", type="secondary"):
        st.session_state.clear()
        st.session_state["current_page"] = "conference_login"
        st.rerun()


# =====================================================
# Load Company Bookings
# =====================================================
def get_company_bookings():
    conn = db_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.*, u.name AS booked_by, u.department
        FROM conference_bookings b
        JOIN conference_users u ON u.id = b.user_id
        WHERE u.company = (
            SELECT company FROM conference_users WHERE id=%s
        )
        ORDER BY b.start_time DESC
    """, (st.session_state["user_id"],))
    return cursor.fetchall()


# =====================================================
# Dashboard Rendering
# =====================================================
def render_dashboard():

    load_css()
    render_header()

    bookings = get_company_bookings()

    st.markdown("### Booking List")

    col1, col2 = st.columns([2,1])

    # ---- LEFT : Table ----
    with col1:
        if not bookings:
            st.info("No bookings found.")
        else:
            df = pd.DataFrame(bookings)

            df["Date"] = pd.to_datetime(df["start_time"]).dt.date
            df["Time"] = (
                pd.to_datetime(df["start_time"]).dt.strftime("%I:%M %p") +
                " — " +
                pd.to_datetime(df["end_time"]).dt.strftime("%I:%M %p")
            )

            df = df[["booked_by", "department", "Date", "Time", "purpose"]]
            df.index = df.index + 1
            df.index.name = "S.No"

            st.dataframe(
                df,
                use_container_width=True,
                height=420
            )

    # ---- RIGHT : Summary ----
    with col2:
        st.markdown("### Summary")

        today = datetime.today().date()
        todays_count = sum(1 for b in bookings if b["booking_date"] == today)

        st.metric("Today's Bookings", todays_count)
        st.metric("Total Bookings", len(bookings))

        st.write("---")

        # Department breakdown
        st.write("#### By Department")
        dept_map = {}
        for b in bookings:
            dept_map[b["department"]] = dept_map.get(b["department"], 0) + 1

        for dept, count in dept_map.items():
            st.metric(dept, count)


# =====================================================
# Page Entry
# =====================================================
def conference_dashboard():
    if "user_id" not in st.session_state:
        st.session_state["current_page"] = "conference_login"
        st.rerun()

    render_dashboard()
