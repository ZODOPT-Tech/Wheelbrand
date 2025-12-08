import streamlit as st
from datetime import datetime, timedelta, time
import mysql.connector
import boto3
import json

# ==================
# CONFIG
# ==================
AWS_REGION = "ap-south-1"
SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_COLOR = "#50309D"
BUTTON_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"

DEPARTMENTS = ["Select", "Sales", "HR", "Finance", "Tech", "Digital Marketing", "IT"]
PURPOSES = ["Select", "Client Visit", "Internal Meeting", "HOD Meeting", "Induction", "Training"]

WORK_START = time(9, 30)
WORK_END = time(19, 0)


# ==================
# DB CONNECTION
# ==================
@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    secret = client.get_secret_value(SecretId=SECRET_NAME)
    return json.loads(secret["SecretString"])


@st.cache_resource
def get_conn():
    c = get_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True,
    )


# --------------------------
# Fetch Bookings for user
# --------------------------
def get_bookings(user_id):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM conference_bookings
        WHERE user_id = %s
        ORDER BY start_time ASC
    """, (user_id,))
    return cur.fetchall()


# --------------------------
# Save Booking
# --------------------------
def save_booking(user_id, date, start, end, dept, purpose):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO conference_bookings (user_id, booking_date, start_time, end_time, department, purpose)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, date, start, end, dept, purpose))

    return True


# --------------------------
# Cancel Booking
# --------------------------
def cancel_booking(booking_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM conference_bookings WHERE id = %s", (booking_id,))
    return True


# --------------------------
# Update Booking
# --------------------------
def update_booking(bid, start, end):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE conference_bookings
        SET start_time=%s, end_time=%s
        WHERE id=%s
    """, (start, end, bid))
    return True


# ==================
# UI HEADER
# ==================
def header(title="Conference Room Booking"):
    st.markdown(f"""
    <style>
        header[data-testid="stHeader"] {{display:none;}}
        .block-container {{padding-top:0 !important;}}

        .header-box {{
            background:{BUTTON_GRADIENT};
            padding:18px 28px;
            margin:-1rem -1rem 1rem -1rem;
            border-radius:12px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            box-shadow:0 6px 16px rgba(0,0,0,0.15);
        }}
        .title-text {{
            font-size:25px;
            font-weight:800;
            color:white;
        }}
        .logo-img {{
            height:42px;
        }}

        .purple-btn>button {{
            background:{BUTTON_GRADIENT} !important;
            border:none !important;
            color:white !important;
            width:100%;
            font-weight:600;
            border-radius:8px !important;
            padding:8px 0 !important;
        }}

        .card {{
            background:white;
            border-radius:12px;
            padding:16px 16px;
            box-shadow:0 3px 10px rgba(0,0,0,0.09);
            margin-bottom:6px;
        }}

        /* SLIDING PANEL */
        .modal-overlay {{
            position:fixed;
            top:0; left:0;
            width:100%; height:100%;
            background:rgba(0,0,0,0.45);
            backdrop-filter:blur(2px);
            display:flex;
            justify-content:flex-end;
            z-index:1000;
        }}
        .modal-content {{
            width:360px;
            background:white;
            height:100%;
            padding:18px;
            border-radius:6px 0 0 6px;
            animation:slideIn 0.3s;
        }}
        @keyframes slideIn {{
            from {{transform:translateX(400px);}}
            to {{transform:translateX(0);}}
        }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="header-box">
            <div class="title-text">{title}</div>
            <img src="{LOGO_URL}" class="logo-img"/>
        </div>
    """, unsafe_allow_html=True)


# ==================
# TIMESLOTS
# ==================
def time_slots(date):
    slots = ["Select"]
    now = datetime.now()
    dt = datetime.combine(date, WORK_START)
    end = datetime.combine(date, WORK_END)

    while dt <= end:
        # Disable past times
        if dt > now:
            slots.append(dt.strftime("%I:%M %p"))
        dt += timedelta(minutes=30)
    return slots


# ==================
# MAIN PAGE
# ==================
def render_booking_page():

    if "user_id" not in st.session_state:
        st.warning("Login first")
        return

    header("Conference Room Booking")

    colL, colR = st.columns([2, 1], gap="large")

    # ============================
    # LEFT CALENDAR PLACEHOLDER
    # ============================
    with colL:
        st.subheader("Schedule")
        st.info("Calendar UI here (FullCalendar).")
        st.write("This is where the calendar appears…")

    # ============================
    # RIGHT FORM
    # ============================
    with colR:
        st.subheader("Create Booking")

        today = datetime.today().date()

        with st.form("book"):
            date = st.date_input("Meeting Date", today)
            stime = st.selectbox("Start Time", time_slots(date))
            etime = st.selectbox("End Time", time_slots(date))
            dept = st.selectbox("Department", DEPARTMENTS)
            purpose = st.selectbox("Purpose", PURPOSES)

            submitted = st.form_submit_button("Confirm Booking")

            if submitted:
                if "Select" in [stime, etime, dept, purpose]:
                    st.error("Fill all fields.")
                else:
                    start = datetime.combine(date, datetime.strptime(stime, "%I:%M %p").time())
                    end = datetime.combine(date, datetime.strptime(etime, "%I:%M %p").time())

                    if end <= start:
                        st.error("End time must be after start.")
                    else:
                        save_booking(st.session_state.user_id, date, start, end, dept, purpose)
                        st.success("Booking Successful!")
                        st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Back to Dashboard"):
            st.session_state.current_page = "conference_dashboard"
            st.rerun()

    # ============================
    # MY BOOKINGS
    # ============================
    st.write("---")
    st.subheader("My Bookings")

    bookings = get_bookings(st.session_state.user_id)
    if not bookings:
        st.info("No bookings yet.")
        return

    for b in bookings:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Date**:", b["booking_date"])
                st.write("**Time**:",
                         b["start_time"].strftime("%I:%M %p"),
                         " - ",
                         b["end_time"].strftime("%I:%M %p"))

            with col2:
                st.write("**Department**:", b["department"])
                st.write("**Purpose**:", b["purpose"])

            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("Edit", key=f"edit_{b['id']}"):
                    st.session_state["edit_id"] = b["id"]
                    st.session_state["edit_start"] = b["start_time"]
                    st.session_state["edit_end"] = b["end_time"]

            with c2:
                if st.button("Cancel", key=f"cancel_{b['id']}"):
                    cancel_booking(b["id"])
                    st.success("Cancelled.")
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

    # ============================
    # EDIT SLIDING PANEL
    # ============================
    edit_id = st.session_state.get("edit_id")
    if edit_id:
        # overlay
        with st.container():
            st.markdown('<div class="modal-overlay">', unsafe_allow_html=True)
            st.markdown('<div class="modal-content">', unsafe_allow_html=True)

            st.subheader("Edit Booking")

            # get booking data
            booking = [x for x in bookings if x["id"] == edit_id][0]
            date = booking["booking_date"]
            start_now = booking["start_time"].strftime("%I:%M %p")
            end_now = booking["end_time"].strftime("%I:%M %p")

            stime = st.selectbox("Start Time",
                                 time_slots(date),
                                 index=time_slots(date).index(start_now), key="edit_st")
            etime = st.selectbox("End Time",
                                 time_slots(date),
                                 index=time_slots(date).index(end_now), key="edit_et")

            if st.button("Save Changes"):
                ns = datetime.combine(date, datetime.strptime(stime, "%I:%M %p").time())
                ne = datetime.combine(date, datetime.strptime(etime, "%I:%M %p").time())

                if ne <= ns:
                    st.error("Invalid time")
                else:
                    update_booking(edit_id, ns, ne)
                    st.success("Updated")
                    st.session_state["edit_id"] = None
                    st.rerun()

            if st.button("Close"):
                st.session_state["edit_id"] = None
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
