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
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"


# -------------------------------------------------------
# HEADER COMPONENT
# -------------------------------------------------------
def render_header():
    username = st.session_state.get("user_name", "")
    company = st.session_state.get("company", "")

    st.markdown(f"""
        <style>
        header[data-testid="stHeader"] {{display:none!important;}}
        .block-container {{padding-top:0;}}

        .header-box {{
            background:{HEADER_GRADIENT};
            padding:22px 32px;
            margin:-1rem -1rem 1.5rem -1rem;
            border-radius:18px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            box-shadow:0 4px 20px rgba(0,0,0,0.18);
        }}

        .header-left {{
            display:flex;
            flex-direction:column;
        }}

        .header-title {{
            color:white;
            font-size:28px;
            font-weight:800;
            margin-bottom:3px;
        }}

        .header-sub {{
            color:white;
            opacity:0.85;
            font-size:16px;
            font-weight:500;
        }}

        .header-right {{
            display:flex;
            align-items:center;
            gap:20px;
        }}

        .header-logo {{
            height:48px;
        }}

        .logout-icon-button {{
            width:34px;
            cursor:pointer;
            transition:0.3s;
        }}
        .logout-icon-button:hover {{
            filter:brightness(200%);
        }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="header-box">
            <div class="header-left">
                <div class="header-title">Welcome, {company}</div>
                <div class="header-sub">{username}</div>
            </div>

            <div class="header-right">
                <img class="header-logo" src="{LOGO_URL}"/>

                <img class="logout-icon-button" 
                     src="https://cdn-icons-png.flaticon.com/512/1828/1828490.png"
                     onclick="window.location.href='?logout=true';"/>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Handle logout
    if st.experimental_get_query_params().get("logout"):
        st.session_state.clear()
        st.session_state['current_page'] = 'conference_login'
        st.experimental_set_query_params()
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
    render_header()

    company = st.session_state.get("company")
    bookings = load_company_bookings(company)

    st.button("➕ New Booking", use_container_width=True, 
              on_click=lambda: go_to_booking_page())

    st.write("")

    col_left, col_right = st.columns([2, 1])

    # ---------------------------------------------------
    # LEFT SIDE TABLE
    # ---------------------------------------------------
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

            st.dataframe(df, use_container_width=True, height=420)


    # ---------------------------------------------------
    # RIGHT SIDE SUMMARY
    # ---------------------------------------------------
    with col_right:
        st.subheader("📊 Summary")

        today = datetime.today().date()

        today_bookings = [b for b in bookings if b.get("booking_date") == today]

        st.metric("Today's Bookings", len(today_bookings))
        st.metric("Total Bookings", len(bookings))

        # Departments count
        st.markdown("---")
        st.write("#### By Department")

        dept_counts = {}
        for b in bookings:
            dept_counts[b["department"]] = dept_counts.get(b["department"], 0) + 1

        for dept, count in dept_counts.items():
            st.metric(dept, count)

        # Purpose statistics
        st.markdown("---")
        st.write("#### By Purpose")
        purpose_count = {}
        for b in bookings:
            p = b["purpose"]
            purpose_count[p] = purpose_count.get(p, 0) + 1

        for p, count in purpose_count.items():
            st.metric(p, count)


# ---------------------------------------------------
# PAGE NAVIGATION (CALLBACK)
# ---------------------------------------------------
def go_to_booking_page():
    st.session_state['current_page'] = "conference_bookings"
    st.rerun()
