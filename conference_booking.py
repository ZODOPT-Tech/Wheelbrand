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
    c = conn.cursor(dictionary=True)
    c.execute("""
        SELECT * FROM conference_bookings
        WHERE user_id=%s 
        ORDER BY booking_date DESC, start_time ASC
    """, (user_id,))
    return c.fetchall()


def save_booking(user_id, booking_date, start_dt, end_dt, dept, purpose):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO conference_bookings
        (user_id, booking_date, start_time, end_time, department, purpose)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (user_id, booking_date, start_dt, end_dt, dept, purpose))
    return True


def delete_booking(bid, user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM conference_bookings WHERE id=%s AND user_id=%s",
              (bid, user_id))


# ==============================
# Update Booking
# ==============================
def update_booking(bid, user_id, nd, ns, ne, ndp, npp):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE conference_bookings
        SET booking_date=%s,
            start_time=%s,
            end_time=%s,
            department=%s,
            purpose=%s
        WHERE id=%s AND user_id=%s
    """,
    (
        nd,
        datetime.combine(nd, ns),
        datetime.combine(nd, ne),
        ndp,
        npp,
        bid,
        user_id
    ))


# ==============================
# Calendar Events Builder
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
# TIME SLOTS
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
        header[data-testid="stHeader"] {{display:none;}}
        .block-container {{padding-top:0rem;}}

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
        .logo {{
            height:48px;
        }}

        .booking-row {{
            background:#F6F3FF;
            border-radius:10px;
            padding:12px 14px;
            margin-bottom:10px;
            display:flex;
            justify-content:space-between;
        }}
        .btn {{
            background:{HEADER_GRADIENT} !important;
            color:white !important;
            border:none;
            padding:7px 14px;
            border-radius:8px;
            font-size:14px;
            cursor:pointer;
        }}
    </style>
    """, unsafe_allow_html=True)


# ==============================
# MAIN PAGE
# ==============================
def render_booking_page():
    inject_css()

    user_id = st.session_state.get("user_id")
    user_name = st.session_state.get("user_name", "User")

    # ============ HEADER
    st.markdown(f"""
        <div class="header-box">
            <div class="header-title">Conference Booking</div>
            <img class="logo" src="{LOGO_URL}">
        </div>
    """, unsafe_allow_html=True)

    # Layout
    col1, col2 = st.columns([2, 1], gap="large")

    # ========= CALENDAR
    with col1:
        st.subheader("Schedule")

        my_bookings = get_my_bookings(user_id)
        events = prepare_events(my_bookings)

        cal_opts = {
            "headerToolbar": {
                "left": "today prev,next",
                "center": "title",
                "right": "timeGridDay,timeGridWeek",
            },
            "initialView": "timeGridWeek",
            "slotDuration": "00:30:00",
            "slotMinTime": "09:30:00",
            "slotMaxTime": "19:00:00",
            "height": 710,
            "allDaySlot": False,
            "nowIndicator": True,
        }

        calendar(events=events, options=cal_opts, key="cal1")

        st.write("")
        if st.button("Back to Dashboard", type="primary", use_container_width=True):
            st.session_state['current_page'] = "conference_dashboard"
            st.rerun()

    # ========= BOOKING FORM
    with col2:
        st.subheader("New Booking")
        with st.form("form_create"):
            d = st.date_input("Date", date.today())
            start = st.selectbox("Start Time", TIME_OPTIONS, index=0)
            end = st.selectbox("End Time", TIME_OPTIONS, index=0)
            dept = st.selectbox("Department", DEPARTMENTS, index=0)
            purpose = st.selectbox("Purpose", PURPOSES, index=0)

            if st.form_submit_button("Confirm Booking", type="primary"):
                if start == "Select" or end == "Select" or dept == "Select" or purpose == "Select":
                    st.error("All fields required.")
                else:
                    start_t = datetime.strptime(start, "%I:%M %p").time()
                    end_t = datetime.strptime(end, "%I:%M %p").time()

                    if datetime.combine(d, start_t) <= datetime.now():
                        st.error("Cannot book past time.")
                    else:
                        save_booking(
                            user_id,
                            d,
                            datetime.combine(d, start_t),
                            datetime.combine(d, end_t),
                            dept,
                            purpose
                        )
                        st.success("Booking Successful.")
                        st.rerun()

        # ========= MY BOOKINGS
        st.subheader("My Bookings")
        my = get_my_bookings(user_id)

        params = st.query_params

        # CANCEL handler
        if "cancel" in params:
            delete_booking(params["cancel"], user_id)
            st.success("Booking cancelled.")
            st.rerun()

        # EDIT Save handler
        if "save_edit" in params:
            bid = params["save_edit"]
            nd = datetime.strptime(params["ed_date"], "%Y-%m-%d").date()
            ns = datetime.strptime(params["ed_start"], "%I:%M %p").time()
            ne = datetime.strptime(params["ed_end"], "%I:%M %p").time()
            ndp = params["ed_dept"]
            npp = params["ed_purpose"]
            update_booking(bid, user_id, nd, ns, ne, ndp, npp)
            st.success("Updated successfully")
            st.rerun()

        if not my:
            st.info("No bookings found.")
        else:
            for b in my:
                st.markdown(f"""
                <div class="booking-row">
                    <div>
                        <b>{b['booking_date'].strftime("%d %b %Y")}</b><br>
                        {b['start_time'].strftime("%I:%M %p")} - {b['end_time'].strftime("%I:%M %p")}<br>
                        {b['purpose']} | {b['department']}
                    </div>
                    <div>
                        <button class="btn" onClick="window.location.href='?edit={b['id']}'">Edit</button>
                        <button class="btn" onClick="window.location.href='?cancel={b['id']}'">Cancel</button>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Inline EDIT form
                if "edit" in params and params["edit"] == str(b['id']):
                    st.write("---")
                    with st.form(f"edit_form_{b['id']}"):
                        nd = st.date_input("Date", value=b["booking_date"])
                        stime = b["start_time"].strftime("%I:%M %p")
                        etime = b["end_time"].strftime("%I:%M %p")

                        ns = st.selectbox("Start", TIME_OPTIONS, index=TIME_OPTIONS.index(stime))
                        ne = st.selectbox("End", TIME_OPTIONS, index=TIME_OPTIONS.index(etime))

                        ndp = st.selectbox("Department", DEPARTMENTS, index=DEPARTMENTS.index(b['department']))
                        npp = st.selectbox("Purpose", PURPOSES, index=PURPOSES.index(b['purpose']))

                        save = st.form_submit_button("Save Changes", type="primary")

                        if save:
                            # redirect with params to update in same request
                            st.query_params = {
                                "save_edit": b['id'],
                                "ed_date": nd,
                                "ed_start": ns,
                                "ed_end": ne,
                                "ed_dept": ndp,
                                "ed_purpose": npp
                            }
                            st.rerun()
