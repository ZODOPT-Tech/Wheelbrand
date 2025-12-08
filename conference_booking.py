import streamlit as st
import boto3
import json
import mysql.connector
from datetime import datetime, time, timedelta
from streamlit_calendar import calendar


# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"

WORK_START = time(9, 30)
WORK_END = time(19, 0)

DEPT_OPTIONS = ["Sales", "HR", "Finance", "Tech", "Marketing", "Admin"]
PURPOSE_OPTIONS = ["Client Visit", "Internal Meeting", "HOD Meeting", "Training"]


# ---------------------------------------------------------------------
# DB HELPERS
# ---------------------------------------------------------------------

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


# ---------------------------------------------------------------------
# HEADER UI
# ---------------------------------------------------------------------

def render_header():
    st.markdown(f"""
    <style>
        header[data-testid="stHeader"] {{
            display: none !important;
        }}
        .block-container {{
            padding-top: 0rem !important;
        }}
        .header-box {{
            background: {HEADER_GRADIENT};
            padding: 18px 32px;
            margin: -1rem -1rem 1rem -1rem;
            border-radius: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 5px 14px rgba(0,0,0,0.14);
        }}
        .header-title {{
            font-size: 24px;
            font-weight: 700;
            color: white;
            font-family: Inter, sans-serif;
        }}
        .header-right {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}
        .back-btn {{
            background: white;
            color: #50309D;
            font-weight: 600;
            border: none;
            padding: 6px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 15px;
        }}
        .logo-img {{
            height: 42px;
        }}
    </style>
    """, unsafe_allow_html=True)

    # Functional back button
    with st.container():
        cols = st.columns([9, 1])
        with cols[1]:
            if st.button("← Back", key="goBack"):
                st.session_state["current_page"] = "conference_dashboard"
                st.rerun()

    # Styled header
    st.markdown(f"""
        <div class="header-box">
            <div class="header-title">Conference Booking</div>
            <div class="header-right">
                <button class="back-btn" onclick="document.querySelector('button[key=goBack]').click()">
                    Back
                </button>
                <img src="{LOGO_URL}" class="logo-img">
            </div>
        </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------
# TIME SLOT FILTER
# ---------------------------------------------------------------------

def available_times(meeting_date):
    options = []
    now = datetime.now()

    slot = datetime.combine(meeting_date, WORK_START)
    end = datetime.combine(meeting_date, WORK_END)

    while slot <= end:
        if meeting_date > now.date():  # future day
            options.append(slot.strftime("%I:%M %p"))
        else:  # today
            if slot.time() > now.time():
                options.append(slot.strftime("%I:%M %p"))
        slot += timedelta(minutes=30)

    return options


# ---------------------------------------------------------------------
# FETCH EVENTS FOR CALENDAR
# ---------------------------------------------------------------------

def fetch_events():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM conference_bookings")
    rows = cur.fetchall()

    events = []
    for r in rows:
        events.append({
            "title": f"{r['purpose']} ({r['department']})",
            "start": r["start_time"].isoformat(),
            "end": r["end_time"].isoformat(),
            "color": "#7A42FF"
        })
    return events


# ---------------------------------------------------------------------
# FETCH USER BOOKINGS
# ---------------------------------------------------------------------

def fetch_my_bookings():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM conference_bookings
        WHERE user_id=%s ORDER BY start_time ASC
    """, (st.session_state["user_id"],))
    return cur.fetchall()


# ---------------------------------------------------------------------
# SAVE BOOKING
# ---------------------------------------------------------------------

def save_booking(meeting_date, start_str, end_str, dept, purpose):
    conn = get_conn()
    cur = conn.cursor()

    booking_date = datetime.today().date()
    start_time = datetime.strptime(start_str, "%I:%M %p").time()
    end_time = datetime.strptime(end_str, "%I:%M %p").time()

    start_dt = datetime.combine(meeting_date, start_time)
    end_dt = datetime.combine(meeting_date, end_time)

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
        booking_date,
        start_dt,
        end_dt,
        dept,
        purpose
    ))
    conn.commit()
    return True


# ---------------------------------------------------------------------
# DELETE BOOKING
# ---------------------------------------------------------------------

def delete_booking(bid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM conference_bookings WHERE id=%s AND user_id=%s",
                (bid, st.session_state["user_id"]))
    conn.commit()


# ---------------------------------------------------------------------
# UPDATE BOOKING
# ---------------------------------------------------------------------

def update_booking(bid, new_start, new_end, meeting_date):
    conn = get_conn()
    cur = conn.cursor()

    ns = datetime.strptime(new_start, "%I:%M %p").time()
    ne = datetime.strptime(new_end, "%I:%M %p").time()

    ns_dt = datetime.combine(meeting_date, ns)
    ne_dt = datetime.combine(meeting_date, ne)

    cur.execute("""
        UPDATE conference_bookings
        SET start_time=%s, end_time=%s
        WHERE id=%s AND user_id=%s
    """, (ns_dt, ne_dt, bid, st.session_state["user_id"]))
    conn.commit()


# ---------------------------------------------------------------------
# PAGE RENDER
# ---------------------------------------------------------------------

def render_booking_page():
    render_header()

    tab1, tab2 = st.tabs(["Book Slot", "Manage Meetings"])

    # -------------------------------------------------------
    # TAB 1 - BOOK SLOT
    # -------------------------------------------------------
    with tab1:
        left, right = st.columns([2, 1])

        # Calendar first
        with left:
            st.subheader("Schedule View")
            calendar(
                events=fetch_events(),
                options={
                    "initialView": "timeGridDay",
                    "slotMinTime": "09:30:00",
                    "slotMaxTime": "19:00:00",
                    "slotDuration": "00:30:00",
                    "height": 650,
                    "headerToolbar": {
                        "left": "prev,next today",
                        "center": "title",
                        "right": "timeGridDay,timeGridWeek"
                    },
                },
                key="cal",
            )

        # Booking form
        with right:
            st.subheader("Create Booking")

            meeting_date = st.date_input("Meeting Date", datetime.today().date())
            start_opt = available_times(meeting_date)
            end_opt = available_times(meeting_date)

            start_time = st.selectbox("Start Time", start_opt)
            end_time = st.selectbox("End Time", end_opt)

            dept = st.selectbox("Department", DEPT_OPTIONS)
            purpose = st.selectbox("Purpose", PURPOSE_OPTIONS)

            if st.button("Confirm Booking", use_container_width=True):
                if save_booking(meeting_date, start_time, end_time, dept, purpose):
                    st.success("Booking Successful.")
                    st.session_state["current_page"] = "conference_dashboard"
                    st.rerun()

    # -------------------------------------------------------
    # TAB 2 - MANAGE MEETINGS
    # -------------------------------------------------------
    with tab2:
        st.subheader("Your Meetings")

        bookings = fetch_my_bookings()
        if not bookings:
            st.info("No meetings found.")
        else:
            for b in bookings:
                st.markdown("---")
                st.text(f"Date: {b['start_time'].strftime('%d %b %Y')}")
                st.text(
                    f"Time: {b['start_time'].strftime('%I:%M %p')} - "
                    f"{b['end_time'].strftime('%I:%M %p')}"
                )
                st.text(f"Department: {b['department']}")
                st.text(f"Purpose: {b['purpose']}")

                c1, c2 = st.columns(2)
                with c1:
                    if st.button(f"Cancel #{b['id']}", key=f"D{b['id']}"):
                        delete_booking(b["id"])
                        st.rerun()
                with c2:
                    if st.button(f"Edit #{b['id']}", key=f"E{b['id']}"):
                        st.session_state["edit_id"] = b["id"]
                        st.rerun()

                # Edit mode
                if "edit_id" in st.session_state and st.session_state["edit_id"] == b["id"]:
                    st.info("Edit Booking Time")
                    ns = st.selectbox(
                        "New Start Time",
                        available_times(b["booking_date"]),
                        key=f"ns{b['id']}"
                    )
                    ne = st.selectbox(
                        "New End Time",
                        available_times(b["booking_date"]),
                        key=f"ne{b['id']}"
                    )

                    if st.button("Update", key=f"U{b['id']}"):
                        update_booking(b["id"], ns, ne, b["booking_date"])
                        del st.session_state["edit_id"]
                        st.success("Updated successfully.")
                        st.rerun()
