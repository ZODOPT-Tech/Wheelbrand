import streamlit as st
import boto3
import json
import mysql.connector
from datetime import datetime, date, time, timedelta
from streamlit_calendar import calendar


# ======================================================
# CONFIG
# ======================================================

AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"

WORK_START = time(9, 30)
WORK_END = time(19, 0)

DEPARTMENTS = ["Sales", "HR", "Finance", "Tech", "Marketing", "Admin"]
PURPOSES = ["Client Visit", "Internal Meeting", "HOD Meeting", "Training"]


# ======================================================
# DB HELPERS
# ======================================================

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


# ======================================================
# HEADER UI
# ======================================================

def header():
    st.markdown(f"""
    <style>
        header[data-testid="stHeader"] {{ display:none !important; }}
        .block-container {{ padding-top:0rem !important; }}

        .header-box {{
            background:{HEADER_GRADIENT};
            padding:20px 32px;
            margin:-1rem -1rem 1rem -1rem;
            border-radius:16px;
            display:flex;
            justify-content:flex-start;
            align-items:center;
            gap:14px;
            box-shadow:0 6px 16px rgba(0,0,0,0.15);
        }}

        .header-title {{
            font-size:26px;
            font-weight:700;
            color:white;
            font-family:Inter, sans-serif;
        }}

        .logo-img {{
            height:42px;
            border-radius:6px;
        }}

        .purple > button {{
            background:{HEADER_GRADIENT} !important;
            color:white !important;
            border:none !important;
            font-weight:600 !important;
            border-radius:8px !important;
            height:45px !important;
            font-size:15px;
        }}

        .purple > button:hover {{
            opacity:0.92;
        }}

    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="header-box">
        <div class="header-title">Conference Booking</div>
        <img src="{LOGO_URL}" class="logo-img">
    </div>
    """, unsafe_allow_html=True)


# ======================================================
# TIME SLOTS
# ======================================================

def future_slots(dt):
    now = datetime.now()
    slots = []
    t = datetime.combine(dt, WORK_START)
    while t <= datetime.combine(dt, WORK_END):
        if dt > now.date() or t.time() > now.time():
            slots.append(t.strftime("%I:%M %p"))
        t += timedelta(minutes=30)
    return slots


# ======================================================
# EVENTS FOR CALENDAR
# ======================================================

def fetch_events():
    conn = get_conn()
    c = conn.cursor(dictionary=True)
    c.execute("SELECT department, purpose, start_time, end_time FROM conference_bookings")
    data = c.fetchall()
    return [
        {
            "title": f"{r['purpose']} ({r['department']})",
            "start": r["start_time"].isoformat(),
            "end": r["end_time"].isoformat(),
            "color": "#7A42FF",
        }
        for r in data
    ]


# ======================================================
# SAVE BOOKING
# ======================================================

def save_booking(meeting_date, start_str, end_str, dept, purpose):
    conn = get_conn()
    c = conn.cursor()

    booking_date = date.today()
    start_dt = datetime.combine(meeting_date, datetime.strptime(start_str, "%I:%M %p").time())
    end_dt = datetime.combine(meeting_date, datetime.strptime(end_str, "%I:%M %p").time())

    # Check overlap
    c.execute("""
        SELECT 1 FROM conference_bookings
        WHERE booking_date=%s
        AND (%s < end_time AND %s > start_time)
    """, (meeting_date, start_dt, end_dt))

    if c.fetchone():
        st.error("This time slot is already booked.")
        return False

    c.execute("""
        INSERT INTO conference_bookings
        (user_id, booking_date, start_time, end_time, department, purpose)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        st.session_state["user_id"],
        booking_date,
        start_dt,
        end_dt,
        dept,
        purpose,
    ))
    return True


# ======================================================
# MAIN PAGE RENDER
# ======================================================

def render_booking_page():
    header()

    col1, col2 = st.columns([2.2, 1], gap="large")

    # ================= LEFT: Calendar =================
    with col1:
        st.subheader("Schedule")
        calendar(
            events=fetch_events(),
            options={
                "initialView": "timeGridDay",
                "slotMinTime": "09:30:00",
                "slotMaxTime": "19:00:00",
                "slotDuration": "00:30:00",
                "height": 720,
                "headerToolbar": {
                    "left": "prev,next today",
                    "center": "title",
                    "right": "timeGridDay,timeGridWeek"
                },
            },
            key="calendar",
        )

    # ================= RIGHT: Booking Form =============
    with col2:
        st.subheader("Create Booking")

        meeting_date = st.date_input("Meeting Date", date.today())
        start_options = future_slots(meeting_date)
        start_time = st.selectbox("Start Time", start_options)

        end_options = [
            t for t in start_options
            if datetime.strptime(t, "%I:%M %p") > datetime.strptime(start_time, "%I:%M %p")
        ]
        end_time = st.selectbox("End Time", end_options)

        dept = st.selectbox("Department", DEPARTMENTS)
        purpose = st.selectbox("Purpose", PURPOSES)

        st.write("")
        st.write("")

        # Confirm Button
        st.markdown('<div class="purple">', unsafe_allow_html=True)
        if st.button("Confirm Booking", use_container_width=True):
            if save_booking(meeting_date, start_time, end_time, dept, purpose):
                st.success("Booking Successful.")
                st.session_state["current_page"] = "conference_dashboard"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.write("")

        # Back Button
        st.markdown('<div class="purple">', unsafe_allow_html=True)
        if st.button("Back to Dashboard", use_container_width=True):
            st.session_state["current_page"] = "conference_dashboard"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
