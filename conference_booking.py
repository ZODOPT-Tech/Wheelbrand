import streamlit as st
import mysql.connector
import boto3, json
from datetime import datetime, date, time, timedelta
from streamlit_calendar import calendar


# ========================= CONFIG =========================
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

WORK_START = time(9, 30)
WORK_END = time(19, 0)

DEPARTMENTS = ["Select", "Sales", "HR", "Finance", "Delivery/Tech", "Digital Marketing", "IT"]
PURPOSES = ["Select", "Client Visit", "Internal Meeting", "HOD Meeting", "Inductions", "Training"]


# ======================= DB CONNECTION =======================
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


# ========================= DB HELPERS =========================
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
    """, (new_start, new_end, bid, user_id))


def delete_booking(bid, user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM conference_bookings WHERE id=%s AND user_id=%s",
                (bid, user_id))


# ========================= TIME SLOTS =========================
def all_time_slots():
    slots = []
    current = datetime.combine(date.today(), WORK_START)
    end = datetime.combine(date.today(), WORK_END)
    while current <= end:
        slots.append(current.strftime("%I:%M %p"))
        current += timedelta(minutes=30)
    return slots


FULL_TIME_OPTIONS = ["Select"] + all_time_slots()


def filtered_time_options(selected_date: date):
    """Return only valid time options (exclude past)"""
    now = datetime.now()
    today = date.today()

    if selected_date != today:
        return FULL_TIME_OPTIONS

    valid = ["Select"]
    for t in FULL_TIME_OPTIONS[1:]:
        slot_time = datetime.combine(today, datetime.strptime(t, "%I:%M %p").time())
        if slot_time > now:
            valid.append(t)
    return valid


# ========================= CALENDAR =========================
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


# ========================= CSS =========================
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

        .logo {{height:48px;}}

        .booking-card {{
            background:white;
            border-radius:14px;
            padding:16px;
            box-shadow:0 2px 12px rgba(0,0,0,0.08);
            margin-bottom:14px;
        }}

        .btn {{
            background:{HEADER_GRADIENT} !important;
            color:white !important;
            border:none;
            padding:7px 14px;
            border-radius:8px;
            margin-top:6px;
        }}
    </style>
    """, unsafe_allow_html=True)


# ========================= MAIN PAGE =========================
def render_booking_page():
    inject_css()

    if "edit_id" not in st.session_state:
        st.session_state.edit_id = None

    user_id = st.session_state.get("user_id")

    # HEADER
    st.markdown(f"""
        <div class="header-box">
            <div class="header-title">Conference Booking</div>
            <img src="{LOGO_URL}" class="logo"/>
        </div>
    """, unsafe_allow_html=True)


    # LAYOUT
    col_calendar, col_form = st.columns([2, 1])


    # ================= CALENDAR ==================
    with col_calendar:
        bookings = get_my_bookings(user_id)
        events = prepare_events(bookings)

        calendar(events=events, options={
            "initialView": "timeGridWeek",
            "slotDuration": "00:30:00",
            "slotMinTime": "09:30:00",
            "slotMaxTime": "19:00:00",
            "height": 700,
        })

        if st.button("Back to Dashboard", use_container_width=True):
            st.session_state["current_page"] = "conference_dashboard"
            st.rerun()


    # ================= NEW BOOKING ==================
    with col_form:
        st.subheader("Create Booking")

        selected_date = st.date_input("Date", date.today())
        time_opts = filtered_time_options(selected_date)

        with st.form("create_form"):
            start = st.selectbox("Start", time_opts)
            end = st.selectbox("End", time_opts)
            dept = st.selectbox("Department", DEPARTMENTS)
            purpose = st.selectbox("Purpose", PURPOSES)

            submit = st.form_submit_button("Confirm Booking")

            if submit:
                if start=="Select" or end=="Select" or dept=="Select" or purpose=="Select":
                    st.error("Fill all fields")
                else:
                    st_t = datetime.strptime(start, "%I:%M %p").time()
                    en_t = datetime.strptime(end, "%I:%M %p").time()

                    save_booking(
                        user_id,
                        selected_date,
                        datetime.combine(selected_date, st_t),
                        datetime.combine(selected_date, en_t),
                        dept,
                        purpose
                    )
                    st.success("Booking Saved")
                    st.rerun()


        # ================= MY BOOKINGS ==================
        st.subheader("My Bookings")

        my = get_my_bookings(user_id)

        if not my:
            st.info("No bookings")
        else:
            for b in my:
                st.markdown("<div class='booking-card'>", unsafe_allow_html=True)

                st.write(
                    f"**{b['booking_date'].strftime('%d %b %Y')}**\n"
                    f"{b['start_time'].strftime('%I:%M %p')} - {b['end_time'].strftime('%I:%M %p')}\n"
                    f"{b['purpose']} | {b['department']}"
                )

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Edit", key=f"edit_{b['id']}"):
                        st.session_state.edit_id = b["id"]
                        st.rerun()
                with c2:
                    if st.button("Cancel", key=f"cancel_{b['id']}"):
                        delete_booking(b["id"], user_id)
                        st.success("Deleted")
                        st.rerun()

                # ===== INLINE EDIT =====
                if st.session_state.edit_id == b["id"]:
                    st.write("---")
                    with st.form(f"edit_form_{b['id']}"):

                        slot_date = b['booking_date']
                        slot_opts = filtered_time_options(slot_date)

                        start_str = b['start_time'].strftime("%I:%M %p")
                        end_str = b['end_time'].strftime("%I:%M %p")

                        si = slot_opts.index(start_str) if start_str in slot_opts else 0
                        ei = slot_opts.index(end_str) if end_str in slot_opts else 0

                        ns = st.selectbox("Start", slot_opts, index=si)
                        ne = st.selectbox("End", slot_opts, index=ei)

                        save = st.form_submit_button("Save")

                        if save:
                            new_start = datetime.strptime(ns, "%I:%M %p").time()
                            new_end = datetime.strptime(ne, "%I:%M %p").time()

                            update_booking_time(
                                b["id"], user_id,
                                datetime.combine(slot_date, new_start),
                                datetime.combine(slot_date, new_end)
                            )
                            st.success("Updated")
                            st.session_state.edit_id = None
                            st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)
