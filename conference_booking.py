import streamlit as st
import mysql.connector
import boto3
import json
from datetime import datetime, date, time, timedelta
from streamlit_calendar import calendar


# ================= CONFIG =================
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg,#50309D,#7A42FF)"

AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

WORK_START = time(9, 30)
WORK_END = time(19, 0)

DEPARTMENTS = [
    "Select", "Sales", "HR", "Finance",
    "Delivery/Tech", "Digital Marketing", "IT", "Tech"
]

PURPOSES = [
    "Select", "Client Visit", "Internal Meeting",
    "HOD Meeting", "Inductions", "Training"
]


# ================= DB CONNECTION =================
@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    raw = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(raw["SecretString"])


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


# ================= DB HELPERS =================
def get_my_bookings(uid):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM conference_bookings
        WHERE user_id=%s
        ORDER BY booking_date DESC,start_time ASC
    """, (uid,))
    return cur.fetchall()


def save_booking(uid, d, s, e, dept, purpose):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO conference_bookings
        (user_id,booking_date,start_time,end_time,department,purpose)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (uid, d, s, e, dept, purpose))


def delete_booking(bid, uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM conference_bookings WHERE id=%s AND user_id=%s", (bid, uid))


def update_booking_time(bid, uid, s, e):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE conference_bookings 
        SET start_time=%s,end_time=%s
        WHERE id=%s AND user_id=%s
    """, (s, e, bid, uid))


# ================= TIME SLOT LOGIC =================
def generate_slots(d: date):
    now = datetime.now()
    slots = ["Select"]

    start_dt = datetime.combine(d, WORK_START)
    end_dt = datetime.combine(d, WORK_END)
    cur = start_dt

    while cur <= end_dt:
        # Today => only future slots
        if d == date.today():
            if cur > now + timedelta(minutes=1):
                slots.append(cur.strftime("%I:%M %p"))
        else:
            slots.append(cur.strftime("%I:%M %p"))

        cur += timedelta(minutes=30)

    return slots


# ================= CALENDAR EVENTS =================
def prepare_events(rows):
    return [
        {
            "id": str(b["id"]),
            "title": b["purpose"],
            "start": b["start_time"].isoformat(),
            "end": b["end_time"].isoformat(),
            "color": "#50309D",
        }
        for b in rows
    ]


# ================= CSS =================
def inject_css():
    st.markdown(f"""
    <style>
    header[data-testid="stHeader"] {{display:none;}}
    .block-container {{padding-top:0;}}

    .header-box {{
        background:{HEADER_GRADIENT};
        padding:22px 38px;
        margin:-1rem -1rem 1.2rem -1rem;
        border-radius:16px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 6px 14px rgba(0,0,0,0.16);
    }}
    .header-title {{
        color:white;
        font-size:28px;
        font-weight:800;
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
        border-radius:8px;
        padding:6px 12px;
        width:100%;
    }}
    </style>
    """, unsafe_allow_html=True)


# ================= MAIN RENDER =================
def render_booking_page():
    inject_css()

    # track edit state
    if "edit_id" not in st.session_state:
        st.session_state.edit_id = None

    user_id = st.session_state.get("user_id")

    # ===== HEADER =====
    st.markdown(f"""
    <div class="header-box">
        <div class="header-title">Conference Booking</div>
        <img src="{LOGO_URL}" class="logo"/>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([2, 1])

    # ===== CALENDAR =====
    with col_left:
        my = get_my_bookings(user_id)
        events = prepare_events(my)

        calendar(
            events=events,
            options={
                "initialView": "timeGridWeek",
                "slotMinTime":"09:30:00",
                "slotMaxTime":"19:00:00",
                "slotDuration":"00:30:00",
                "height":700,
            }
        )

        if st.button("Back to Dashboard", use_container_width=True):
            st.session_state["current_page"] = "conference_dashboard"
            st.rerun()

    # ===== BOOK FORM =====
    with col_right:
        st.subheader("Create Booking")

        sel_d = st.date_input("Date", date.today())
        opts = generate_slots(sel_d)

        with st.form("new_book"):
            s = st.selectbox("Start", opts)
            e = st.selectbox("End", opts)
            dept = st.selectbox("Department", DEPARTMENTS)
            pp = st.selectbox("Purpose", PURPOSES)

            if st.form_submit_button("Confirm Booking"):
                if s=="Select" or e=="Select" or dept=="Select" or pp=="Select":
                    st.error("All fields required")
                else:
                    sdt = datetime.combine(sel_d, datetime.strptime(s, "%I:%M %p").time())
                    edt = datetime.combine(sel_d, datetime.strptime(e, "%I:%M %p").time())
                    save_booking(user_id, sel_d, sdt, edt, dept, pp)
                    st.success("Booked")
                    st.rerun()

    # ===== LIST BOOKINGS BELOW =====
    st.subheader("My Bookings")

    rows = get_my_bookings(user_id)
    if not rows:
        st.info("No Bookings yet")
        return

    for b in rows:
        st.markdown("<div class='booking-card'>", unsafe_allow_html=True)

        st.write(
            f"**{b['booking_date'].strftime('%d %b %Y')}**  "
            f"{b['start_time'].strftime('%I:%M %p')} - "
            f"{b['end_time'].strftime('%I:%M %p')}  "
            f"{b['purpose']} | {b['department']}"
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Edit", key=f"e{b['id']}"):
                st.session_state.edit_id = b['id']
                st.rerun()
        with c2:
            if st.button("Cancel", key=f"c{b['id']}"):
                delete_booking(b['id'], user_id)
                st.success("Booking cancelled")
                st.rerun()

        # Inline edit
        if st.session_state.edit_id == b['id']:
            st.write("---")
            with st.form(f"edit_{b['id']}"):
                sd = b['booking_date']
                slots = generate_slots(sd)

                s_str = b['start_time'].strftime("%I:%M %p")
                e_str = b['end_time'].strftime("%I:%M %p")

                s_idx = slots.index(s_str) if s_str in slots else 0
                e_idx = slots.index(e_str) if e_str in slots else 0

                ns = st.selectbox("Start", slots, index=s_idx)
                ne = st.selectbox("End", slots, index=e_idx)

                if st.form_submit_button("Save"):
                    ns_t = datetime.combine(sd, datetime.strptime(ns, "%I:%M %p").time())
                    ne_t = datetime.combine(sd, datetime.strptime(ne, "%I:%M %p").time())
                    update_booking_time(b['id'], user_id, ns_t, ne_t)
                    st.success("Updated")
                    st.session_state.edit_id = None
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
