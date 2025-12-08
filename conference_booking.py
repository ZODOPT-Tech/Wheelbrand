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

DEPARTMENTS = ["Select", "Sales", "HR", "Finance", "Tech", "Marketing", "Admin"]
PURPOSES = ["Select", "Client Visit", "Internal Meeting", "HOD Meeting", "Training"]


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


def get_user_bookings():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, booking_date, start_time, end_time, department, purpose
        FROM conference_bookings
        WHERE user_id=%s
        ORDER BY booking_date DESC, start_time DESC
    """, (st.session_state["user_id"],))
    return cur.fetchall()


# ======================================================
# HEADER
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
            justify-content:space-between;
            align-items:center;
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
# CALENDAR EVENTS
# ======================================================

def fetch_events():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT department, purpose, start_time, end_time FROM conference_bookings")
    data = cur.fetchall()
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
# TIME SLOTS
# ======================================================

def future_slots(dt):
    now = datetime.now()
    slots = ["Select"]
    t = datetime.combine(dt, WORK_START)
    end = datetime.combine(dt, WORK_END)
    while t <= end:
        if dt > now.date() or t.time() > now.time():
            slots.append(t.strftime("%I:%M %p"))
        t += timedelta(minutes=30)
    return slots


# ======================================================
# SAVE / UPDATE / DELETE
# ======================================================

def save_booking(meeting_date, start_str, end_str, dept, purpose):
    conn = get_conn()
    cur = conn.cursor()
    start_dt = datetime.combine(meeting_date, datetime.strptime(start_str, "%I:%M %p").time())
    end_dt = datetime.combine(meeting_date, datetime.strptime(end_str, "%I:%M %p").time())

    # Overlap check
    cur.execute("""
        SELECT 1 FROM conference_bookings
        WHERE booking_date=%s
        AND (%s < end_time AND %s > start_time)
    """, (meeting_date, start_dt, end_dt))
    if cur.fetchone():
        st.error("This time slot is already booked.")
        return False

    cur.execute("""
        INSERT INTO conference_bookings
        (user_id, booking_date, start_time, end_time, department, purpose)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        st.session_state["user_id"],
        date.today(),
        start_dt,
        end_dt,
        dept,
        purpose,
    ))
    return True


def delete_booking(booking_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM conference_bookings WHERE id=%s AND user_id=%s",
                (booking_id, st.session_state["user_id"]))


def update_booking(booking_id, dt, new_start, new_end):
    conn = get_conn()
    cur = conn.cursor()

    # overlap
    cur.execute("""
        SELECT 1 FROM conference_bookings
        WHERE user_id=%s
        AND id!=%s
        AND booking_date=%s
        AND (%s < end_time AND %s > start_time)
    """, (st.session_state["user_id"], booking_id, dt, new_start, new_end))
    if cur.fetchone():
        st.error("Overlapping with another booking.")
        return False

    cur.execute("""
        UPDATE conference_bookings
        SET start_time=%s, end_time=%s
        WHERE id=%s AND user_id=%s
    """, (new_start, new_end, booking_id, st.session_state["user_id"]))
    return True


# ======================================================
# EDIT UI
# ======================================================

def edit_ui(b):
    st.subheader("Edit Booking")

    dt = b["booking_date"]
    slots = []
    t = datetime.combine(dt, WORK_START)
    end = datetime.combine(dt, WORK_END)
    while t <= end:
        slots.append(t.strftime("%I:%M %p"))
        t += timedelta(minutes=30)

    current_start = b["start_time"].strftime("%I:%M %p")
    current_end = b["end_time"].strftime("%I:%M %p")

    new_start = st.selectbox("Start Time", slots, index=slots.index(current_start))
    new_end = st.selectbox("End Time", slots, index=slots.index(current_end))

    st.markdown('<div class="purple">', unsafe_allow_html=True)
    if st.button("Save Changes"):
        ns = datetime.combine(dt, datetime.strptime(new_start, "%I:%M %p").time())
        ne = datetime.combine(dt, datetime.strptime(new_end, "%I:%M %p").time())
        if ne <= ns:
            st.error("End time must be after start.")
            return
        if update_booking(b['id'], dt, ns, ne):
            st.success("Updated successfully.")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ======================================================
# MAIN PAGE
# ======================================================

def render_booking_page():
    header()

    col1, col2 = st.columns([2.2, 1], gap="large")

    # ------------- LEFT: Calendar -------------
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
            },
            key="calendar",
        )

    # ------------- RIGHT: Create Booking ------
    with col2:
        st.subheader("Create Booking")

        meeting_date = st.date_input("Meeting Date", date.today())

        start_opts = future_slots(meeting_date)
        start_time = st.selectbox("Start Time", start_opts)

        if start_time != "Select":
            end_opts = ["Select"] + [
                t for t in start_opts if t != "Select" and
                datetime.strptime(t, "%I:%M %p") > datetime.strptime(start_time, "%I:%M %p")
            ]
        else:
            end_opts = ["Select"]

        end_time = st.selectbox("End Time", end_opts)
        dept = st.selectbox("Department", DEPARTMENTS)
        purpose = st.selectbox("Purpose", PURPOSES)

        st.markdown('<div class="purple">', unsafe_allow_html=True)
        if st.button("Confirm Booking", use_container_width=True):
            if start_time == "Select" or end_time == "Select":
                st.warning("Select valid time.")
            elif dept == "Select" or purpose == "Select":
                st.warning("Fill all fields.")
            else:
                if save_booking(meeting_date, start_time, end_time, dept, purpose):
                    st.success("Booking Successful.")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="purple">', unsafe_allow_html=True)
        if st.button("Back to Dashboard", use_container_width=True):
            st.session_state["current_page"] = "conference_dashboard"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- MY BOOKINGS ----------------
    st.subheader("My Bookings")

    bookings = get_user_bookings()
    if not bookings:
        st.info("No bookings created yet.")
        return

    for b in bookings:
        with st.container():
            colA, colB, colC = st.columns([3,3,2])

            with colA:
                st.write(f"**Date:** {b['booking_date']}")
                st.write(f"**Time:** {b['start_time'].strftime('%I:%M %p')} - {b['end_time'].strftime('%I:%M %p')}")

            with colB:
                st.write(f"**Department:** {b['department']}")
                st.write(f"**Purpose:** {b['purpose']}")

            with colC:
                st.markdown('<div class="purple">', unsafe_allow_html=True)
                if st.button("Edit", key=f"edit_{b['id']}"):
                    edit_ui(b)
                if st.button("Cancel", key=f"del_{b['id']}"):
                    delete_booking(b['id'])
                    st.success("Canceled.")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
