import streamlit as st
import mysql.connector
import boto3, json
from datetime import datetime, date, time, timedelta
from streamlit_calendar import calendar

# ==============================
# CONFIG
# ==============================
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

WORK_START = time(9, 30)
WORK_END = time(19, 0)

DEPARTMENTS = ["Select", "Sales", "HR", "Finance", "Delivery/Tech", "Digital Marketing", "IT"]
PURPOSES = ["Select", "Client Visit", "Internal Meeting", "HOD Meeting", "Inductions", "Training"]


# ==============================
# AWS DB Connection
# ==============================
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


# ==============================
# DB Helpers
# ==============================
def get_my_bookings(user_id):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM conference_bookings
        WHERE user_id=%s
        ORDER BY booking_date DESC, start_time ASC
    """, (user_id,))
    return cur.fetchall()


def save_booking(user_id, booking_date, start_dt, end_dt, dept, purpose):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO conference_bookings
        (user_id, booking_date, start_time, end_time, department, purpose)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (user_id, booking_date, start_dt, end_dt, dept, purpose))


def update_booking_time(bid, user_id, new_start, new_end):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE conference_bookings
        SET start_time=%s,
            end_time=%s
        WHERE id=%s AND user_id=%s
    """,
    (new_start, new_end, bid, user_id))


def delete_booking(bid, user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM conference_bookings WHERE id=%s AND user_id=%s",
                (bid, user_id))


# ==============================
# Calendar Events
# ==============================
def prepare_events(bookings):
    events = []
    for b in bookings:
        events.append({
            "id": str(b["id"]),
            "title": b["purpose"],
            "start": b["start_time"].isoformat(),
            "end": b["end_time"].isoformat(),
            "color": "#50309D",
        })
    return events


# ==============================
# TIME OPTIONS
# ==============================
def time_slots():
    slots = ["Select"]
    current = datetime.combine(date.today(), WORK_START)
    end = datetime.combine(date.today(), WORK_END)
    while current <= end:
        slots.append(current.strftime("%I:%M %p"))
        current += timedelta(minutes=30)
    return slots


TIME_OPTIONS = time_slots()


# ==============================
# CSS
# ==============================
def inject_css():
    st.markdown(f"""
    <style>
        header[data-testid="stHeader"] {{ display:none; }}
        .block-container {{ padding-top:0rem; }}

        .header-box {{
            background:{HEADER_GRADIENT};
            padding:24px 40px;
            margin:-1rem -1rem 1rem -1rem;
            border-radius:18px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            box-shadow:0 6px 14px rgba(0,0,0,0.18);
        }}
        .header-title {{
            font-size:28px;
            font-weight:800;
            color:white;
        }}
        .logo {{ height:48px; }}

        .btn {{
            background:{HEADER_GRADIENT} !important;
            color:white !important;
            border:none;
            padding:6px 12px;
            border-radius:8px;
        }}

        .booking-item {{
            background:#F6F3FF;
            border-radius:10px;
            padding:14px;
            margin-bottom:12px;
        }}
    </style>
    """, unsafe_allow_html=True)


# ==============================
# MAIN
# ==============================
def render_booking_page():
    inject_css()

    if "edit_id" not in st.session_state:
        st.session_state.edit_id = None

    user_id = st.session_state.get("user_id")
    username = st.session_state.get("user_name", "User")


    # HEADER
    st.markdown(f"""
        <div class="header-box">
            <div class="header-title">Conference Booking</div>
            <img src="{LOGO_URL}" class="logo"/>
        </div>
    """, unsafe_allow_html=True)


    # LAYOUT
    col_calendar, col_form = st.columns([2, 1], gap="large")


    # ======================
    # CALENDAR
    # ======================
    with col_calendar:
        st.subheader("Calendar")

        bookings = get_my_bookings(user_id)
        events = prepare_events(bookings)

        calendar(events=events, options={
            "initialView": "timeGridWeek",
            "slotDuration": "00:30:00",
            "slotMinTime": "09:30:00",
            "slotMaxTime": "19:00:00",
            "height": 710,
        })

        if st.button("Back to Dashboard", use_container_width=True):
            st.session_state['current_page'] = "conference_dashboard"
            st.rerun()


    # ======================
    # BOOKING FORM
    # ======================
    with col_form:
        st.subheader("New Booking")

        with st.form("create"):
            d = st.date_input("Date", date.today())
            s = st.selectbox("Start", TIME_OPTIONS)
            e = st.selectbox("End", TIME_OPTIONS)
            dept = st.selectbox("Department", DEPARTMENTS)
            purpose = st.selectbox("Purpose", PURPOSES)

            submit = st.form_submit_button("Confirm Booking")

            if submit:
                if s=="Select" or e=="Select" or dept=="Select" or purpose=="Select":
                    st.error("All fields required.")
                else:
                    start_t = datetime.strptime(s, "%I:%M %p").time()
                    end_t = datetime.strptime(e, "%I:%M %p").time()

                    if datetime.combine(d, start_t) <= datetime.now():
                        st.error("Cannot book past time")
                    else:
                        save_booking(
                            user_id,
                            d,
                            datetime.combine(d, start_t),
                            datetime.combine(d, end_t),
                            dept,
                            purpose
                        )
                        st.success("Booking Saved.")
                        st.rerun()


        # ======================
        # MY BOOKINGS
        # ======================
        st.subheader("My Bookings")

        my = get_my_bookings(user_id)
        if not my:
            st.info("No bookings found")
        else:
            for b in my:
                st.markdown("<div class='booking-item'>", unsafe_allow_html=True)

                st.write(
                    f"**{b['booking_date'].strftime('%d %b %Y')}**\n"
                    f"{b['start_time'].strftime('%I:%M %p')} - "
                    f"{b['end_time'].strftime('%I:%M %p')}\n"
                    f"{b['purpose']} | {b['department']}"
                )

                c1, c2 = st.columns([1,1])
                with c1:
                    if st.button("Edit", key=f"edit_{b['id']}"):
                        st.session_state.edit_id = b['id']
                        st.rerun()

                with c2:
                    if st.button("Cancel", key=f"del_{b['id']}"):
                        delete_booking(b["id"], user_id)
                        st.success("Booking cancelled")
                        st.rerun()

                # ========= INLINE EDIT =========
                if st.session_state.edit_id == b['id']:
                    st.write("---")
                    with st.form(f"form_edit_{b['id']}"):
                        start_str = b['start_time'].strftime("%I:%M %p")
                        end_str = b['end_time'].strftime("%I:%M %p")

                        # safe dropdown index
                        s_index = TIME_OPTIONS.index(start_str) if start_str in TIME_OPTIONS else 0
                        e_index = TIME_OPTIONS.index(end_str) if end_str in TIME_OPTIONS else 0

                        ns = st.selectbox("Start", TIME_OPTIONS, index=s_index)
                        ne = st.selectbox("End", TIME_OPTIONS, index=e_index)

                        save = st.form_submit_button("Save")

                        if save:
                            new_s = datetime.strptime(ns, "%I:%M %p").time()
                            new_e = datetime.strptime(ne, "%I:%M %p").time()

                            update_booking_time(
                                b['id'],
                                user_id,
                                datetime.combine(b['booking_date'], new_s),
                                datetime.combine(b['booking_date'], new_e)
                            )
                            st.success("Booking updated")
                            st.session_state.edit_id = None
                            st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)
