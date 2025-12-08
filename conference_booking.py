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


# ========================= DB =========================
@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    return json.loads(client.get_secret_value(SecretId=AWS_SECRET_NAME)["SecretString"])


@st.cache_resource
def get_conn():
    c = get_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True
    )


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


def update_booking_time(bid, user_id, start_dt, end_dt):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE conference_bookings
        SET start_time=%s, end_time=%s
        WHERE id=%s AND user_id=%s
    """, (start_dt, end_dt, bid, user_id))


def delete_booking(bid, user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM conference_bookings WHERE id=%s AND user_id=%s", (bid, user_id))


# ========================= SLOT FILTER =========================
def generate_slots(selected_date: date):
    """
    Always remove past time slots for the same day.
    If selected date > today → show full list.
    """
    now = datetime.now()
    slots = ["Select"]

    start_dt = datetime.combine(selected_date, WORK_START)
    end_dt = datetime.combine(selected_date, WORK_END)

    current = start_dt
    while current <= end_dt:
        # future slots only when today
        if selected_date > date.today() or current > now + timedelta(minutes=1):
            slots.append(current.strftime("%I:%M %p"))
        current += timedelta(minutes=30)

    return slots


# ========================= EVENTS =========================
def prepare_events(bookings):
    return [
        {
            "id": str(b["id"]),
            "title": b["purpose"],
            "start": b["start_time"].isoformat(),
            "end": b["end_time"].isoformat(),
            "color": "#50309D",
        }
        for b in bookings
    ]


# ========================= CSS =========================
def inject_css():
    st.markdown(f"""
    <style>
        header[data-testid="stHeader"] {{display:none;}}
        .block-container {{padding-top:0rem;}}

        .header-box {{
            background:{HEADER_GRADIENT};
            padding:22px 36px;
            margin:-1rem -1rem 1rem -1rem;
            border-radius:18px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            box-shadow:0 6px 14px rgba(0,0,0,0.18);
        }}

        .header-title {{
            font-size:27px;
            font-weight:800;
            color:white;
        }}

        .logo {{height:46px;}}

        .booking-card {{
            background:white;
            border-radius:14px;
            padding:16px;
            box-shadow:0 2px 12px rgba(0,0,0,0.08);
            margin-bottom:16px;
        }}

        .btn {{
            background:{HEADER_GRADIENT} !important;
            color:white !important;
            border:none;
            padding:6px 14px;
            border-radius:8px;
            width:100%;
        }}
    </style>
    """, unsafe_allow_html=True)


# ========================= MAIN =========================
def render_booking_page():
    inject_css()

    if "edit_id" not in st.session_state:
        st.session_state.edit_id = None

    user_id = st.session_state.get("user_id")

    # ========== HEADER ==========
    st.markdown(f"""
        <div class="header-box">
            <div class="header-title">Conference Booking</div>
            <img src="{LOGO_URL}" class="logo"/>
        </div>
    """, unsafe_allow_html=True)


    # ========== LAYOUT ==========
    col_cal, col_create = st.columns([2, 1])


    # ======= CALENDAR =======
    with col_cal:
        books = get_my_bookings(user_id)
        events = prepare_events(books)

        calendar(
            events=events,
            options={
                "initialView": "timeGridWeek",
                "slotDuration": "00:30:00",
                "slotMinTime": "09:30:00",
                "slotMaxTime": "19:00:00",
                "height": 700,
            }
        )

        if st.button("Back to Dashboard", use_container_width=True):
            st.session_state["current_page"] = "conference_dashboard"
            st.rerun()


    # ======= CREATE =======
    with col_create:
        st.subheader("Create Booking")

        sel_date = st.date_input("Date", date.today())
        time_opts = generate_slots(sel_date)

        with st.form("create_form"):
            start = st.selectbox("Start Time", time_opts)
            end = st.selectbox("End Time", time_opts)
            dept = st.selectbox("Department", DEPARTMENTS)
            purpose = st.selectbox("Purpose", PURPOSES)

            if st.form_submit_button("Confirm Booking"):
                if start=="Select" or end=="Select" or dept=="Select" or purpose=="Select":
                    st.error("All fields required.")
                else:
                    s = datetime.strptime(start, "%I:%M %p").time()
                    e = datetime.strptime(end, "%I:%M %p").time()

                    save_booking(
                        user_id,
                        sel_date,
                        datetime.combine(sel_date, s),
                        datetime.combine(sel_date, e),
                        dept,
                        purpose
                    )
                    st.success("Booking Successful")
                    st.rerun()


    # ======= MY BOOKINGS =======
    st.subheader("My Bookings")

    my = get_my_bookings(user_id)
    if not my:
        st.info("No bookings yet.")
        return

    # No container around all bookings → each card independent
    for b in my:
        st.markdown("<div class='booking-card'>", unsafe_allow_html=True)

        st.write(
            f"**{b['booking_date'].strftime('%d %b %Y')}**\n"
            f"{b['start_time'].strftime('%I:%M %p')} - {b['end_time'].strftime('%I:%M %p')}\n"
            f"{b['purpose']} | {b['department']}"
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Edit", key=f"e{b['id']}"):
                st.session_state.edit_id = b["id"]
                st.rerun()
        with c2:
            if st.button("Cancel", key=f"c{b['id']}"):
                delete_booking(b["id"], user_id)
                st.success("Booking Cancelled")
                st.rerun()


        # ========== EDIT INLINE ==========
        if st.session_state.edit_id == b["id"]:
            st.write("---")
            with st.form(f"edit{b['id']}"):
                slot_date = b['booking_date']
                slot_opts = generate_slots(slot_date)

                s_str = b['start_time'].strftime("%I:%M %p")
                e_str = b['end_time'].strftime("%I:%M %p")

                s_idx = slot_opts.index(s_str) if s_str in slot_opts else 0
                e_idx = slot_opts.index(e_str) if e_str in slot_opts else 0

                ns = st.selectbox("Start", slot_opts, index=s_idx)
                ne = st.selectbox("End", slot_opts, index=e_idx)

                if st.form_submit_button("Save"):
                    new_s = datetime.strptime(ns, "%I:%M %p").time()
                    new_e = datetime.strptime(ne, "%I:%M %p").time()

                    update_booking_time(
                        b["id"], user_id,
                        datetime.combine(slot_date, new_s),
                        datetime.combine(slot_date, new_e)
                    )
                    st.success("Updated")
                    st.session_state.edit_id = None
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
