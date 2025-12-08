import streamlit as st
from datetime import datetime, timedelta, time
from streamlit_calendar import calendar
import mysql.connector
import boto3
import json

# ------------------------------------------------------
# AWS + DB CONFIG (Your Code)
# ------------------------------------------------------
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

HEADER_GRADIENT = "linear-gradient(90deg, #4B2ECF, #7A42FF)"
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"


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


# ------------------------------------------------------
# CONSTANTS
# ------------------------------------------------------
WORKING_HOUR_START = 9
WORKING_MINUTE_START = 30
WORKING_HOUR_END = 19
WORKING_MINUTE_END = 0

DEPARTMENT_OPTIONS = [
    "Select",
    "Sales",
    "HR",
    "Finance",
    "Delivery/Tech",
    "Digital Marketing",
    "IT",
]

PURPOSE_OPTIONS = [
    "Select",
    "Client Visit",
    "Internal Meeting",
    "HOD Meeting",
    "Inductions",
    "Training",
]


# ------------------------------------------------------
# UTILITY FUNCTIONS
# ------------------------------------------------------
def _get_time_slots(selected_date):
    today = datetime.now().date()
    now = datetime.now()

    slots = ["Select"]
    start_dt = datetime(1, 1, 1, WORKING_HOUR_START, WORKING_MINUTE_START)
    end_dt = datetime(1, 1, 1, WORKING_HOUR_END, WORKING_MINUTE_END)

    while start_dt <= end_dt:
        label = start_dt.strftime("%I:%M %p")

        # Mark past time as unavailable
        if selected_date == today:
            if datetime.combine(today, start_dt.time()) <= now:
                label += " (Unavailable)"

        slots.append(label)
        start_dt += timedelta(minutes=30)

    return slots


def _prepare_events():
    """Load events from DB into calendar format"""
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT cu.name, cu.department,
               cb.purpose, cb.start_time, cb.end_time
        FROM conference_bookings cb
        JOIN conference_users cu ON cu.id = cb.user_id
        ORDER BY start_time ASC
    """)

    rows = cursor.fetchall()
    cursor.close()

    events = []
    for i, r in enumerate(rows):
        events.append({
            "id": str(i),
            "title": f"{r['purpose']} ({r['department']})",
            "start": r['start_time'].isoformat(),
            "end": r['end_time'].isoformat(),
            "color": "#FF4B4B",
        })

    return events


def _save_booking(date, start_str, end_str, dept, purpose):
    now = datetime.now()
    today = now.date()

    # Remove unavailable tag
    start_str = start_str.replace(" (Unavailable)", "")
    end_str = end_str.replace(" (Unavailable)", "")

    # Validate inputs
    if start_str == "Select" or end_str == "Select":
        st.error("Select valid start/end time.")
        return

    if "(Unavailable)" in start_str or "(Unavailable)" in end_str:
        st.error("You cannot book past slots.")
        return

    if dept == "Select" or purpose == "Select":
        st.error("Select Department and Purpose.")
        return

    start = datetime.combine(date, datetime.strptime(start_str, "%I:%M %p").time())
    end = datetime.combine(date, datetime.strptime(end_str, "%I:%M %p").time())

    if date < today:
        st.error("Cannot book past dates.")
        return

    if date == today and start <= now:
        st.error("Cannot book past time.")
        return

    if end <= start:
        st.error("End time must be greater than start time.")
        return

    min_dt = datetime.combine(date, time(WORKING_HOUR_START, WORKING_MINUTE_START))
    max_dt = datetime.combine(date, time(WORKING_HOUR_END, WORKING_MINUTE_END))

    if start < min_dt or end > max_dt:
        st.error("Booking must be within working hours.")
        return

    # Overlap check from DB
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id FROM conference_bookings
        WHERE (%s < end_time AND %s > start_time)
    """, (start, end))

    if cursor.fetchone():
        st.error("Time slot already booked.")
        cursor.close()
        return

    try:
        cursor.execute("""
            INSERT INTO conference_bookings (user_id, department, purpose, start_time, end_time)
            VALUES (%s, %s, %s, %s, %s)
        """, (st.session_state.get("user_id"), dept, purpose, start, end))

        st.success("Booking Successful 🎉")

    except Exception as e:
        st.error("Failed to save booking.")
        st.write(e)
    finally:
        cursor.close()

    st.experimental_rerun()


# ------------------------------------------------------
# HEADER UI
# ------------------------------------------------------
def _render_header():
    st.markdown(f"""
        <style>
            header[data-testid="stHeader"] {{display:none;}}
            .header-box {{
                background:{HEADER_GRADIENT};
                padding:18px 26px;
                margin:-1rem -1rem 1rem -1rem;
                border-radius:0 0 18px 18px;
                display:flex;
                align-items:center;
                justify-content:space-between;
                box-shadow:0 5px 14px rgba(0,0,0,0.18);
            }}
            .cta-btn {{
                background: rgba(255,255,255,0.25);
                border:1px solid rgba(255,255,255,0.45);
                padding:6px 16px;
                border-radius:8px;
                text-align:center;
                color:white;
                font-weight:700;
                cursor:pointer;
            }}
            .title-text {{
                color:white;font-weight:800;font-size:26px;
            }}
            .logo-img {{height:40px;}}
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.5,6,1])
    with col1:
        if st.button("←", key="back_btn"):
            st.session_state['current_page'] = "conference_dashboard"
            st.rerun()
    with col2:
        st.markdown("<div class='title-text' style='text-align:center;'>Conference Booking</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<img src='{LOGO_URL}' class='logo-img'>", unsafe_allow_html=True)


# ------------------------------------------------------
# MAIN PAGE
# ------------------------------------------------------
def render_booking_page():
    _render_header()

    col1, col2 = st.columns([2, 1])

    # Calendar
    with col1:
        st.subheader("📅 Schedule View")
        calendar(
            events=_prepare_events(),
            options={
                "initialView": "timeGridDay",
                "slotDuration": "00:30:00",
                "slotMinTime": "09:30:00",
                "slotMaxTime": "19:00:00",
                "height": 700,
                "headerToolbar": {
                    "left": "today prev,next",
                    "center": "title",
                    "right": "timeGridDay,timeGridWeek",
                },
            },
            key="calendar",
        )

    # Booking form
    with col2:
        st.subheader("📝 Book a Slot")
        today = datetime.now().date()
        booking_date = st.date_input("Date", today)

        start_options = _get_time_slots(booking_date)
        end_options = _get_time_slots(booking_date)

        start_str = st.selectbox("Start Time", start_options)
        end_str = st.selectbox("End Time", end_options)

        dept = st.selectbox("Department", DEPARTMENT_OPTIONS)
        purpose = st.selectbox("Purpose", PURPOSE_OPTIONS)

        if st.button("Confirm Booking", use_container_width=True):
            _save_booking(booking_date, start_str, end_str, dept, purpose)
