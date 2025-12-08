import streamlit as st
import boto3, json, mysql.connector
from datetime import datetime, time
from streamlit_calendar import calendar

# ---------------- DB ----------------
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

# ---------------- UI ----------------
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"
WORK_START = time(9,30)
WORK_END = time(19,0)


def render_header(title):
    st.markdown(f"""
    <style>
    header[data-testid="stHeader"]{{display:none!important;}}
    .block-container{{padding-top:0rem!important;}}
    .header-box {{
        background:{HEADER_GRADIENT};
        padding:24px 36px;
        margin:-1rem -1rem 1rem -1rem;
        border-radius:18px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 6px 16px rgba(0,0,0,0.18);
    }}
    .back-btn {{
        color:white;
        font-weight:600;
        cursor:pointer;
    }}
    .header-title {{
        font-size:28px;
        font-weight:800;
        color:white;
    }}
    .header-logo {{height:48px;}}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="header-box">
        <div class="back-btn" onclick="window.location.reload()">⬅ Back</div>
        <div class="header-title">{title}</div>
        <img class="header-logo" src="{LOGO_URL}">
    </div>
    """, unsafe_allow_html=True)


def fetch_events():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM conference_bookings")
    rows = cur.fetchall()

    events = []
    for r in rows:
        events.append({
            "title": r['purpose'],
            "start": r['start_time'].isoformat(),
            "end": r['end_time'].isoformat(),
            "color": "#ff4d4d"
        })
    return events


def save_booking(date, start, end, dept, purpose):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO conference_bookings 
        (user_id, booking_date, start_time, end_time, department, purpose)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (st.session_state['user_id'], date, start, end, dept, purpose))
    conn.commit()


def render_booking_page():
    render_header("CONFERENCE BOOKING")

    left, right = st.columns([2,1])

    with left:
        st.subheader("Calendar")
        calendar(events=fetch_events(),
                 options={
                     "initialView":"timeGridDay",
                     "slotMinTime":"09:30:00",
                     "slotMaxTime":"19:00:00"
                 })

    with right:
        st.subheader("Book Slot")

        with st.form("book"):
            date = st.date_input("Date", datetime.today())
            start = st.time_input("Start", WORK_START)
            end = st.time_input("End", WORK_END)
            dept = st.text_input("Department")
            purpose = st.text_input("Purpose")
            submit = st.form_submit_button("Confirm")

            if submit:
                now = datetime.now()
                if date == now.date() and start <= now.time():
                    st.error("Cannot book past time.")
                    return

                if start >= end:
                    st.error("End must be greater than start.")
                    return

                start_dt = datetime.combine(date,start)
                end_dt = datetime.combine(date,end)

                save_booking(date, start_dt, end_dt, dept, purpose)
                st.success("Booking Successful")
                st.session_state['current_page'] = 'conference_dashboard'
                st.rerun()
