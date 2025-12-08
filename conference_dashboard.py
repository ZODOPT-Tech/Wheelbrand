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
# HEADER COMPONENT
# -------------------------------------------------------
def render_header():
    username = st.session_state.get("user_name", "")
    company = st.session_state.get("company", "")

    st.markdown(f"""
        <style>
            header[data-testid="stHeader"]{{display:none!important;}}
            .block-container{{padding-top:0;}}

            .header-box {{
                background:{HEADER_GRADIENT};
                padding:24px 36px;
                margin:-1rem -1rem 2rem -1rem;
                border-radius:18px;
                display:flex;
                justify-content:space-between;
                align-items:center;
                box-shadow:0 6px 16px rgba(0,0,0,0.18);
            }}
            .header-left {{
                display:flex;
                flex-direction:column;
            }}
            .header-username {{
                font-size:30px;
                font-weight:800;
                color:white;
                margin-bottom:3px;
            }}
            .header-company {{
                font-size:17px;
                font-weight:500;
                color:white;
                opacity:0.9;
            }}
            .header-right {{
                display:flex;
                align-items:center;
                gap:18px;
            }}
            .header-logo {{
                height:48px;
            }}
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([6, 1])

    with col1:
        st.markdown(
            f"<div class='header-box'>"
            f"<div class='header-left'>"
            f"<div class='header-username'>Welcome, {username}</div>"
            f"<div class='header-company'>{company}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col2:
        if st.button("Logout"):
            st.session_state.clear()
            st.session_state['current_page'] = 'conference_login'
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

    if st.button("New Booking Registration", use_container_width=True):
        st.session_state['current_page'] = "conference_bookings"
        st.rerun()

    st.write("")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Booking List")

        if not bookings:
            st.info("No bookings added yet.")
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

            st.dataframe(df, use_container_width=True, height=400)

    with col_right:
        st.subheader("Summary")

        today = datetime.today().date()
        today_count = len([b for b in bookings if b.get("booking_date") == today])
        total_count = len(bookings)

        st.metric("Today", today_count)
        st.metric("Total", total_count)

        st.write("---")

        # Department-wise counts
        by_dept = {}
        for b in bookings:
            dept = b.get("department")
            by_dept[dept] = by_dept.get(dept, 0) + 1

        for dept, count in by_dept.items():
            st.metric(dept, count)
