import streamlit as st
import mysql.connector
import boto3
import json
import smtplib
from email.mime.text import MIMEText
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


# ================= SECRETS =================
@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    raw = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(raw["SecretString"])


# ================= EMAIL =================
def send_email(to_email, subject, body):
    creds = get_credentials()

    try:
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = creds["SMTP_USER"]
        msg["To"] = to_email

        if int(creds["SMTP_PORT"]) == 465:
            server = smtplib.SMTP_SSL(creds["SMTP_HOST"], int(creds["SMTP_PORT"]))
        else:
            server = smtplib.SMTP(creds["SMTP_HOST"], int(creds["SMTP_PORT"]))
            server.starttls()

        server.login(creds["SMTP_USER"], creds["SMTP_PASSWORD"])
        server.sendmail(creds["SMTP_USER"], to_email, msg.as_string())
        server.quit()

        return True
    except Exception as e:
        st.error(f"Email send failed: {e}")
        return False


# ================= DB =================
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


def get_my_bookings(uid):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT *
        FROM conference_bookings
        WHERE user_id=%s
        ORDER BY booking_date DESC, start_time ASC
    """, (uid,))
    return cur.fetchall()


def save_booking(uid, d, s, e, dept, purpose):
    conn = get_conn()
    cur = conn.cursor()

    # Insert booking
    cur.execute("""
        INSERT INTO conference_bookings
            (user_id, booking_date, start_time, end_time, department, purpose)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (uid, d, s, e, dept, purpose))

    # Fetch user info
    cur.execute("SELECT name, email FROM conference_users WHERE id=%s", (uid,))
    u = cur.fetchone()

    if u:
        uname, email = u

        subject = "Conference Room Booking Confirmation"
        body = f"""
Hello {uname},

Your conference room booking is confirmed.

📅 Date: {d.strftime('%d-%m-%Y')}
⏰ Time: {s.strftime('%I:%M %p')} - {e.strftime('%I:%M %p')}
🏢 Department: {dept}
📝 Purpose: {purpose}

Thank you,
ZODOPT MeetEase Team
"""

        send_email(email, subject, body)


def delete_booking(bid, uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM conference_bookings
        WHERE id=%s AND user_id=%s
    """, (bid, uid))


def update_booking_time(bid, uid, s, e):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE conference_bookings 
        SET start_time=%s, end_time=%s
        WHERE id=%s AND user_id=%s
    """, (s, e, bid, uid))


# ================= TIME SLOTS =================
def generate_slots(selected_date: date):
    now = datetime.now()
    slots = ["Select"]

    start_dt = datetime.combine(selected_date, WORK_START)
    end_dt = datetime.combine(selected_date, WORK_END)

    cur = start_dt
    while cur <= end_dt:
        label = cur.strftime("%I:%M %p")

        if selected_date == date.today():
            if cur > now:
                slots.append(label)
        else:
            slots.append(label)

        cur += timedelta(minutes=30)

    return slots


# ================= EVENTS =================
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
def css():
    st.markdown(f"""
    <style>
    header[data-testid="stHeader"] {{display:none;}}
    .block-container {{padding-top:0;}}

    .header-box {{
        background:{HEADER_GRADIENT};
        padding:22px 38px;
        margin:-1rem -1rem 1rem -1rem;
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

    .booking-item {{
        background:white;
        border-radius:14px;
        padding:14px;
        box-shadow:0 2px 10px rgba(0,0,0,0.08);
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


# ================= MAIN PAGE =================
def render_booking_page():
    css()

    if "edit_id" not in st.session_state:
        st.session_state.edit_id = None

    uid = st.session_state.get("user_id")

    # -------- HEADER --------
    st.markdown(f"""
    <div class="header-box">
        <div class="header-title">Conference Booking</div>
        <img src="{LOGO_URL}" class="logo"/>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([2, 1])

    # ================= LEFT - CALENDAR =================
    with col_left:
        rows = get_my_bookings(uid)

        today_rows = [
            b for b in rows
            if b["booking_date"] == date.today()
        ]

        events = prepare_events(today_rows)

        calendar(
            events=events,
            options={
                "initialView": "timeGridDay",
                "slotMinTime": "09:30:00",
                "slotMaxTime": "19:00:00",
                "slotDuration": "00:30:00",
                "height": 700,
            }
        )

        if st.button("Back to Dashboard", use_container_width=True):
            st.session_state["current_page"] = "conference_dashboard"
            st.rerun()

    # ================= RIGHT SIDE =================
    with col_right:

        # -------- BOOKING FORM --------
        st.subheader("Book a Slot")

        sel_d = date.today()   # only today allowed
        opts = generate_slots(sel_d)

        with st.form("book"):
            s = st.selectbox("Start Time", opts)
            e = st.selectbox("End Time", opts)
            dept = st.selectbox("Department", DEPARTMENTS)
            pp = st.selectbox("Purpose", PURPOSES)

            if st.form_submit_button("Confirm Booking"):
                if s=="Select" or e=="Select" or dept=="Select" or pp=="Select":
                    st.error("All fields required")
                else:
                    sd = sel_d
                    sdt = datetime.combine(sd, datetime.strptime(s,"%I:%M %p").time())
                    edt = datetime.combine(sd, datetime.strptime(e,"%I:%M %p").time())
                    save_booking(uid, sd, sdt, edt, dept, pp)
                    st.success("Booking Successful — Email Sent!")
                    st.rerun()

        # -------- TODAY'S BOOKINGS --------
        with st.expander("Today's Bookings", expanded=True):

            if not today_rows:
                st.info("No bookings today")
            else:
                for b in today_rows:
                    st.markdown("<div class='booking-item'>", unsafe_allow_html=True)

                    st.write(
                        f"**{b['booking_date'].strftime('%d %b %Y')}**  "
                        f"{b['start_time'].strftime('%I:%M %p')} - {b['end_time'].strftime('%I:%M %p')}  "
                        f"{b['purpose']} | {b['department']}"
                    )

                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Edit", key=f"e{b['id']}"):
                            st.session_state.edit_id = b['id']
                            st.rerun()

                    with c2:
                        if st.button("Cancel", key=f"c{b['id']}"):
                            delete_booking(b['id'], uid)
                            st.success("Booking canceled")
                            st.rerun()

                    # Inline Edit
                    if st.session_state.edit_id == b['id']:
                        st.write("---")
                        with st.form(f"edit_form_{b['id']}"):
                            sd = b['booking_date']
                            slots = generate_slots(sd)

                            s_str = b['start_time'].strftime("%I:%M %p")
                            e_str = b['end_time'].strftime("%I:%M %p")

                            s_idx = slots.index(s_str) if s_str in slots else 0
                            e_idx = slots.index(e_str) if e_str in slots else 0

                            ns = st.selectbox("Start", slots, index=s_idx)
                            ne = st.selectbox("End", slots, index=e_idx)

                            if st.form_submit_button("Save"):
                                ns_t = datetime.combine(sd, datetime.strptime(ns,"%I:%M %p").time())
                                ne_t = datetime.combine(sd, datetime.strptime(ne,"%I:%M %p").time())
                                update_booking_time(b['id'], uid, ns_t, ne_t)
                                st.success("Updated")
                                st.session_state.edit_id = None
                                st.rerun()

                    st.markdown("</div>", unsafe_allow_html=True)
