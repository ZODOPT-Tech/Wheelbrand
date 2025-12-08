import streamlit as st
import boto3
import json
import mysql.connector
from datetime import datetime, time
from streamlit_calendar import calendar

# -------------------- AWS DB CONFIG --------------------
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


# -------------------- UI CONFIG --------------------
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"

WORK_START = time(9,30)
WORK_END = time(19,0)


# -------------------- HEADER --------------------
def render_header():
    st.markdown(f"""
    <style>
    header[data-testid="stHeader"]{{display:none!important;}}
    .block-container{{padding-top:0rem!important;}}
    .header-box {{
        background:{HEADER_GRADIENT};
        padding:24px 36px;
        margin:-1rem -1rem 1rem -1rem;
        border-radius:18px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 6px 16px rgba(0,0,0,0.18);
    }}
    .back-btn {{
        color:white;
        font-weight:700;
        cursor:pointer;
    }}
    .header-title {{
        font-size:28px;
        font-weight:800;
        color:white;
    }}
    .header-logo {{height:48px;}}
    </style>
    """, unsafe_allow_html=True)

    # if you want back button to use navigation
    if st.button("⬅ Back"):
        st.session_state['current_page'] = 'conference_dashboard'
        st.rerun()

    st.markdown(f"""
    <div class="header-box">
        <div class="header-title">Conference Booking</div>
        <img class="header-logo" src="{LOGO_URL}">
    </div>
    """, unsafe_allow_html=True)


# -------------------- FETCH EVENTS --------------------
def fetch_events():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM conference_bookings")
    rows = cur.fetchall()

    events = []
    for r in rows:
        events.append({
            "title": r['purpose'],
            "start": r['start_time'].isoformat(),
            "end": r['end_time'].isoformat(),
            "color": "#ff4d4d"
        })
    return events


# -------------------- SAVE BOOKING --------------------
def save_booking(meeting_date, start_time, end_time, dept, purpose):
    conn = get_conn()
    cur = conn.cursor()

    booking_date = datetime.today().date()  # today
    start_dt = datetime.combine(meeting_date, start_time)
    end_dt   = datetime.combine(meeting_date, end_time)

    # insert values
    cur.execute("""
        INSERT INTO conference_bookings
        (user_id, booking_date, start_time, end_time, department, purpose)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        st.session_state['user_id'],  # from login
        booking_date,
        start_dt,
        end_dt,
        dept,
        purpose
    ))

    conn.commit()


# -------------------- PAGE ENTRY --------------------
def render_booking_page():
    render_header()

    left, right = st.columns([2,1])

    # calendar
    with left:
        st.subheader("📅 Calendar")
        calendar(
            events=fetch_events(),
            options={
                "initialView":"timeGridDay",
                "slotMinTime":"09:30:00",
                "slotMaxTime":"19:00:00",
                "height":700
            }
        )

    # booking form
    with right:
        st.subheader("📝 Book Slot")
        with st.form("book"):
            meeting_date = st.date_input("Meeting Date", datetime.today().date())
            start_time = st.time_input("Start Time", WORK_START)
            end_time   = st.time_input("End Time", WORK_END)
            dept = st.text_input("Department")
            purpose = st.text_input("Purpose")

            submit = st.form_submit_button("Confirm Booking")

            if submit:

                now = datetime.now()
                if meeting_date == now.date() and start_time <= now.time():
                    st.error("Cannot book past time.")
                    return

                if start_time >= end_time:
                    st.error("End time must be after start time.")
                    return

                save_booking(meeting_date, start_time, end_time, dept, purpose)
                st.success("Booking Successful!")
                st.session_state['current_page'] = 'conference_dashboard'
                st.rerun()
