import streamlit as st
import boto3
import json
import mysql.connector
from datetime import datetime, time, timedelta
from streamlit_calendar import calendar

# ------------------------------- AWS DB CONFIG -------------------------------
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

# ------------------------------- STYLE CONFIG --------------------------------
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"

WORK_START = time(9, 30)
WORK_END   = time(19, 0)

DEPT_OPTIONS = ["Sales", "HR", "Finance", "Tech", "Marketing", "Admin"]
PURPOSE_OPTIONS = ["Client Visit", "Internal Meeting", "HOD Meeting", "Training"]


# ---------------------------- HEADER UI --------------------------------------
def render_header():
    st.markdown(f"""
    <style>
        header[data-testid="stHeader"] {{ display:none!important; }}
        .block-container {{ padding-top:0rem!important; }}

        .header-box {{
            background:{HEADER_GRADIENT};
            padding:22px 36px;
            margin:-1rem -1rem 1rem -1rem;
            border-radius:18px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            box-shadow:0 5px 16px rgba(0,0,0,0.16);
        }}

        .title-container {{
            display:flex;
            flex-direction:column;
        }}

        .header-title {{
            font-size:28px;
            font-weight:800;
            color:white;
            margin-bottom:4px;
        }}

        .back-btn {{
            background:white;
            color:#50309D;
            padding:8px 16px;
            font-weight:700;
            border-radius:8px;
            border:none;
            cursor:pointer;
            margin-right:10px;
        }}

        .header-right {{
            display:flex;
            align-items:center;
            gap:12px;
        }}

        .logo-img {{ height:48px; }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="header-box">
            <div class="title-container">
                <div class="header-title">Conference Booking</div>
            </div>
            
            <div class="header-right">
                <button class="back-btn" onclick="window.location.reload();">⬅ Back</button>
                <img src="{LOGO_URL}" class="logo-img" />
            </div>
        </div>
    """, unsafe_allow_html=True)


# ---------------------------- TIME FILTER ------------------------------------
def filtered_time_slots(meeting_date):
    slots = []
    now = datetime.now()

    base = datetime.combine(meeting_date, WORK_START)
    end  = datetime.combine(meeting_date, WORK_END)

    while base <= end:
        if meeting_date > now.date():
            slots.append(base.strftime("%I:%M %p"))
        else:
            if base.time() > now.time():
                slots.append(base.strftime("%I:%M %p"))
        base += timedelta(minutes=30)

    return slots


# ---------------------------- EVENTS FETCH -----------------------------------
def fetch_events():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM conference_bookings")
    rows = cur.fetchall()

    events=[]
    for r in rows:
        events.append({
            "title": f"{r['purpose']} ({r['department']})",
            "start": r["start_time"].isoformat(),
            "end": r["end_time"].isoformat(),
            "color": "#ff4d4d"
        })
    return events


# ---------------------------- MY BOOKINGS ------------------------------------
def fetch_my_bookings():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM conference_bookings
        WHERE user_id=%s ORDER BY start_time ASC
    """,(st.session_state["user_id"],))
    return cur.fetchall()


# ---------------------------- SAVE BOOKING -----------------------------------
def save_booking(meeting_date, start_time_str, end_time_str, dept, purpose):
    conn = get_conn()
    cur = conn.cursor()

    booking_date = datetime.today().date()

    start_time = datetime.strptime(start_time_str,"%I:%M %p").time()
    end_time   = datetime.strptime(end_time_str,"%I:%M %p").time()

    start_dt = datetime.combine(meeting_date,start_time)
    end_dt   = datetime.combine(meeting_date,end_time)

    cur.execute("""
        SELECT * FROM conference_bookings
        WHERE booking_date=%s
        AND (%s < end_time AND %s > start_time)
    """,(meeting_date,start_dt,end_dt))
    
    if cur.fetchone():
        st.error("This time slot is already booked.")
        return False

    cur.execute("""
        INSERT INTO conference_bookings
        (user_id,booking_date,start_time,end_time,department,purpose)
        VALUES (%s,%s,%s,%s,%s,%s)
    """,(st.session_state["user_id"],booking_date,start_dt,end_dt,dept,purpose))
    conn.commit()
    return True


# ---------------------------- DELETE BOOKING -----------------------------------
def delete_booking(bid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM conference_bookings WHERE id=%s AND user_id=%s",(bid,st.session_state["user_id"]))
    conn.commit()


# ---------------------------- EDIT BOOKING -----------------------------------
def update_booking(bid,new_start,new_end,meeting_date):
    conn = get_conn()
    cur = conn.cursor()

    stt = datetime.strptime(new_start,"%I:%M %p").time()
    ett = datetime.strptime(new_end,"%I:%M %p").time()

    start_dt = datetime.combine(meeting_date,stt)
    end_dt   = datetime.combine(meeting_date,ett)

    cur.execute("""
        UPDATE conference_bookings SET start_time=%s,end_time=%s
        WHERE id=%s AND user_id=%s
    """,(start_dt,end_dt,bid,st.session_state["user_id"]))
    conn.commit()


# ---------------------------- RENDER PAGE -----------------------------------
def render_booking_page():
    render_header()

    tab1,tab2 = st.tabs(["📅 Book Slot","🛠 Manage My Meetings"])

    # ================= BOOKING TAB =================
    with tab1:
        col1,col2 = st.columns([2,1])

        with col1:
            st.subheader("Calendar View")
            calendar(events=fetch_events(),options={"height":650})

        with col2:
            st.subheader("Book a Slot")

            meeting_date = st.date_input("Meeting Date",datetime.today().date())

            start_opts = filtered_time_slots(meeting_date)
            end_opts   = filtered_time_slots(meeting_date)

            start_sel = st.selectbox("Start Time",start_opts)
            end_sel   = st.selectbox("End Time",end_opts)

            dept = st.selectbox("Department",DEPT_OPTIONS)
            purpose = st.selectbox("Purpose",PURPOSE_OPTIONS)

            if st.button("Confirm Booking",use_container_width=True):
                ok = save_booking(meeting_date,start_sel,end_sel,dept,purpose)
                if ok:
                    st.success("🎉 Booking Successful!")
                    st.session_state["current_page"]="conference_dashboard"
                    st.rerun()

    # ================= MANAGE TAB =================
    with tab2:
        st.subheader("Your Meetings")

        b_list = fetch_my_bookings()
        if not b_list:
            st.info("No bookings found.")
        else:
            for b in b_list:
                st.write("------------")
                st.write(f"📅 {b['start_time'].strftime('%d %b %Y')}")
                st.write(f"⏰ {b['start_time'].strftime('%I:%M %p')} - {b['end_time'].strftime('%I:%M %p')}")
                st.write(f"🏛 {b['department']}")
                st.write(f"🎯 {b['purpose']}")

                c1,c2 = st.columns(2)
                with c1:
                    if st.button(f"❌ Cancel #{b['id']}",key=f"D{b['id']}"):
                        delete_booking(b["id"])
                        st.rerun()
                with c2:
                    if st.button(f"✏ Edit #{b['id']}",key=f"E{b['id']}"):
                        st.session_state["edit"]=b["id"]
                        st.rerun()

                if "edit" in st.session_state and st.session_state["edit"]==b["id"]:
                    st.info("Editing booking...")
                    ns = st.selectbox("New Start Time",filtered_time_slots(b['booking_date']),key=f"ns{b['id']}")
                    ne = st.selectbox("New End Time",filtered_time_slots(b['booking_date']),key=f"ne{b['id']}")

                    if st.button("Update",key=f"U{b['id']}"):
                        update_booking(b["id"],ns,ne,b["booking_date"])
                        del st.session_state["edit"]
                        st.success("Updated successfully!")
                        st.rerun()
