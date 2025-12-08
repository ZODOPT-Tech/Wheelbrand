import streamlit as st
import boto3
import json
import mysql.connector
from datetime import datetime, date, time, timedelta

# -------------------- AWS DB CONFIG --------------------
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

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


# ================== UI CONSTANTS ==================
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"

WORK_START = time(9,30)
WORK_END = time(19,0)

DEPARTMENTS = [
    "Select",
    "Sales",
    "HR",
    "Finance",
    "Delivery/Tech",
    "Digital Marketing",
    "IT"
]

PURPOSES = [
    "Select",
    "Client Visit",
    "Internal Meeting",
    "HOD Meeting",
    "Inductions",
    "Training"
]


# ================== UTILITIES ==================
def generate_time_slots():
    slots = ["Select"]
    t = datetime(2024,1,1,WORK_START.hour,WORK_START.minute)
    end = datetime(2024,1,1,WORK_END.hour,WORK_END.minute)
    
    while t <= end:
        slots.append(t.strftime("%I:%M %p"))
        t += timedelta(minutes=30)
    return slots


TIME_OPTIONS = generate_time_slots()


def str_to_time(s):
    return datetime.strptime(s, "%I:%M %p").time()


# ================== DB OPERATIONS ==================
def save_booking(meeting_date, start_time, end_time, dept, purpose):
    conn = get_conn()
    cur = conn.cursor()

    booking_date = datetime.today().date()
    start_dt = datetime.combine(meeting_date, start_time)
    end_dt = datetime.combine(meeting_date, end_time)

    # conflict check
    cur.execute("""
        SELECT id FROM conference_bookings
        WHERE booking_date=%s
        AND (%s < end_time AND %s > start_time)
    """, (booking_date, start_dt, end_dt))
    
    if cur.fetchone():
        return False, "Slot already booked."

    cur.execute("""
        INSERT INTO conference_bookings
        (user_id, booking_date, start_time, end_time, department, purpose)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        st.session_state['user_id'],
        booking_date,
        start_dt,
        end_dt,
        dept,
        purpose
    ))

    conn.commit()
    return True, "Booking Successful!"


def load_user_bookings():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM conference_bookings
        WHERE user_id=%s
        ORDER BY start_time DESC
    """, (st.session_state['user_id'],))
    return cur.fetchall()


def cancel_booking(booking_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM conference_bookings WHERE id=%s AND user_id=%s",
                (booking_id, st.session_state['user_id']))
    conn.commit()


def update_booking(booking_id, new_start, new_end):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE conference_bookings
        SET start_time=%s, end_time=%s
        WHERE id=%s AND user_id=%s
    """, (new_start, new_end, booking_id, st.session_state['user_id']))
    conn.commit()


# ================== HEADER ==================
def render_header():
    st.markdown(f"""
    <style>
    header[data-testid="stHeader"]{{display:none!important;}}
    .block-container{{padding-top:0rem!important;}}
    .header-box {{
        background:{HEADER_GRADIENT};
        padding:26px 40px;
        margin:-1rem -1rem 1rem -1rem;
        border-radius:18px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 6px 16px rgba(0,0,0,0.18);
    }}
    .header-title {{
        font-size:30px;
        font-weight:800;
        color:white;
    }}
    .header-right {{
        display:flex;
        align-items:center;
        gap:12px;
    }}
    .back-btn {{
        background:none;
        border:none;
        color:white;
        font-size:16px;
        font-weight:700;
        cursor:pointer;
    }}
    .header-logo {{height:48px;}}
    </style>
    """, unsafe_allow_html=True)

    # Header Bar
    st.markdown(f"""
        <div class="header-box">
            <div class="header-title">Conference Booking</div>
            <div class="header-right">
                <button class="back-btn" type="button" onclick="window.location.reload()">◀ Back</button>
                <img src="{LOGO_URL}" class="header-logo"/>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Back logic
    if st.button(""):
        st.session_state['current_page'] = "conference_dashboard"
        st.rerun()


# ================== MAIN PAGE ==================
def render_booking_page():
    
    render_header()

    st.subheader("📝 Book a Meeting")

    col1, col2 = st.columns([2,1])

    # form
    with col1:
        with st.form("book"):
            meeting_date = st.date_input("Date", date.today())
            start_str = st.selectbox("Start Time", TIME_OPTIONS)
            end_str = st.selectbox("End Time", TIME_OPTIONS)
            dept = st.selectbox("Department", DEPARTMENTS)
            purpose = st.selectbox("Purpose", PURPOSES)

            submit = st.form_submit_button("Confirm Booking")

            if submit:
                if start_str == "Select" or end_str == "Select":
                    st.error("Select valid timings")
                    return

                if dept == "Select":
                    st.error("Select department")
                    return

                if purpose == "Select":
                    st.error("Select purpose")
                    return

                start = str_to_time(start_str)
                end = str_to_time(end_str)

                now = datetime.now()
                if meeting_date == now.date() and start <= now.time():
                    st.error("Cannot book past time")
                    return

                if start >= end:
                    st.error("End must be after start")
                    return

                success, msg = save_booking(meeting_date, start, end, dept, purpose)
                if success:
                    st.success(msg)
                    st.session_state['current_page'] = "conference_dashboard"
                    st.rerun()
                else:
                    st.error(msg)

    # Manage Meetings
    with col2:
        st.subheader("🗂 Manage My Meetings")
        bookings = load_user_bookings()

        if not bookings:
            st.info("No meetings yet.")
        else:
            for b in bookings:
                st.write(f"📅 {b['start_time'].strftime('%d %b %Y')} | {b['start_time'].strftime('%I:%M %p')} - {b['end_time'].strftime('%I:%M %p')}")
                st.write(f"🏢 {b['department']} — {b['purpose']}")

                c1, c2 = st.columns(2)
                if c1.button("Cancel", key=f"cancel_{b['id']}"):
                    cancel_booking(b['id'])
                    st.rerun()

                if c2.button("Edit", key=f"edit_{b['id']}"):
                    new_start_str = st.selectbox("New Start", TIME_OPTIONS, key=f"ns_{b['id']}")
                    new_end_str = st.selectbox("New End", TIME_OPTIONS, key=f"ne_{b['id']}")
                    
                    if new_start_str != "Select" and new_end_str != "Select":
                        ns = str_to_time(new_start_str)
                        ne = str_to_time(new_end_str)
                        update_booking(b['id'],
                                       datetime.combine(b['start_time'].date(), ns),
                                       datetime.combine(b['end_time'].date(), ne))
                        st.rerun()
                st.write("---")
