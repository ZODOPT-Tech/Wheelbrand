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

DEPT_OPTIONS = ["Sales", "HR", "Finance", "Tech", "Marketing", "Admin"]
PURPOSE_OPTIONS = ["Client Visit", "Internal Meeting", "HOD Meeting", "Training"]


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
# HEADER
# ======================================================

def render_header():
    st.markdown(f"""
    <style>
        header[data-testid="stHeader"] {{ display:none !important; }}
        .block-container {{ padding-top:0rem !important; }}

        .header-box {{
            background:{HEADER_GRADIENT};
            padding:18px 32px;
            margin:-1rem -1rem 1rem -1rem;
            border-radius:14px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            box-shadow:0 5px 14px rgba(0,0,0,0.14);
        }}

        .header-title {{
            font-size:24px;
            font-weight:700;
            color:white;
            font-family:Inter,sans-serif;
        }}

        .header-right {{
            display:flex;
            gap:14px;
            align-items:center;
        }}

        .back-btn {{
            background:white;
            border:none;
            padding:6px 16px;
            border-radius:8px;
            color:#50309D;
            font-weight:600;
            cursor:pointer;
            font-size:15px;
        }}

        .logo-img {{ height:42px; }}
    </style>
    """, unsafe_allow_html=True)

    # Header content
    st.markdown(f"""
    <div class="header-box">
        <div class="header-title">Conference Booking</div>
        <div class="header-right">
            <button class="back-btn" onclick="document.getElementById('backBtn').click()">Back</button>
            <img src="{LOGO_URL}" class="logo-img">
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Hidden real back button for python click
    if st.button("BACK", key="backBtn", help="",type="secondary"):
        st.session_state["current_page"] = "conference_dashboard"
        st.rerun()


# ======================================================
# TIME SLOT HANDLING
# ======================================================

def future_slots(meeting_date):
    now = datetime.now()
    slots = []
    slot_dt = datetime.combine(meeting_date, WORK_START)
    last_dt = datetime.combine(meeting_date, WORK_END)

    while slot_dt <= last_dt:
        if meeting_date > now.date():
            slots.append(slot_dt.strftime("%I:%M %p"))
        else:
            if slot_dt.time() > now.time():
                slots.append(slot_dt.strftime("%I:%M %p"))
        slot_dt += timedelta(minutes=30)

    return slots


# ======================================================
# SAVE BOOKING
# ======================================================

def save_booking(meeting_date, start_str, end_str, dept, purpose):
    conn = get_conn()
    cur = conn.cursor()

    booking_date = date.today()

    start_time = datetime.strptime(start_str, "%I:%M %p").time()
    end_time = datetime.strptime(end_str, "%I:%M %p").time()

    start_dt = datetime.combine(meeting_date, start_time)
    end_dt = datetime.combine(meeting_date, end_time)

    # overlap
    cur.execute("""
        SELECT 1 FROM conference_bookings
        WHERE booking_date=%s AND (%s < end_time AND %s > start_time)
    """, (meeting_date, start_dt, end_dt))
    if cur.fetchone():
        st.error("This time slot is already booked.")
        return False

    cur.execute("""
        INSERT INTO conference_bookings
        (user_id, booking_date, start_time, end_time, department, purpose)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (st.session_state["user_id"], booking_date, start_dt, end_dt, dept, purpose))

    return True


# ======================================================
# EVENTS FOR CALENDAR
# ======================================================

def fetch_events():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM conference_bookings")
    rows = cur.fetchall()

    return [{
        "title": f"{r['purpose']} ({r['department']})",
        "start": r["start_time"].isoformat(),
        "end": r["end_time"].isoformat(),
        "color": "#7A42FF"
    } for r in rows]


# ======================================================
# UI PAGE
# ======================================================

def render_booking_page():
    render_header()

    left, right = st.columns([2, 1])

    # -------------------------------------------------- Calendar
    with left:
        st.subheader("Schedule View")
        calendar(
            events=fetch_events(),
            options={
                "initialView": "timeGridDay",
                "slotMinTime": "09:30:00",
                "slotMaxTime": "19:00:00",
                "slotDuration": "00:30:00",
                "height": 680,
                "headerToolbar": {
                    "left":"prev,next today",
                    "center":"title",
                    "right":"timeGridDay,timeGridWeek"
                },
            },
            key="cal",
        )

    # -------------------------------------------------- Form
    with right:
        st.subheader("Create Booking")

        meeting_date = st.date_input("Meeting Date", date.today())

        start_options = future_slots(meeting_date)
        start_time = st.selectbox("Start Time", start_options)

        # End times must be greater than start time
        valid_end = [t for t in start_options if
                     datetime.strptime(t, "%I:%M %p") >
                     datetime.strptime(start_time, "%I:%M %p")]
        end_time = st.selectbox("End Time", valid_end)

        dept = st.selectbox("Department", DEPT_OPTIONS)
        purpose = st.selectbox("Purpose", PURPOSE_OPTIONS)

        if st.button("Confirm Booking", use_container_width=True):
            if save_booking(meeting_date, start_time, end_time, dept, purpose):
                st.success("Booking Successful.")
                st.session_state["current_page"] = "conference_dashboard"
                st.rerun()
