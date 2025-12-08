import streamlit as st
from datetime import datetime, timedelta, time
from streamlit_calendar import calendar

# ---------------- SETTINGS ----------------
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg,#50309D,#7A42FF)"

WORKING_HOUR_START = 9
WORKING_MINUTE_START = 30
WORKING_HOUR_END = 19
WORKING_MINUTE_END = 0

DEPARTMENT_OPTIONS = [
    "Select",
    "Sales",
    "HR",
    "Finance",
    "Delivery/Tech",
    "Digital Marketing",
    "IT"
]

PURPOSE_OPTIONS = [
    "Select",
    "Client Visit",
    "Internal Meeting",
    "HOD Meeting",
    "Inductions",
    "Training"
]


# ------------ Generate Time Slots ------------
def _generate_time_options():
    slots = ["Select"]
    start_dt = datetime(1,1,1,WORKING_HOUR_START,WORKING_MINUTE_START)
    end_dt = datetime(1,1,1,WORKING_HOUR_END,WORKING_MINUTE_END)

    while start_dt <= end_dt:
        slots.append(start_dt.strftime("%I:%M %p"))
        start_dt += timedelta(minutes=30)
    return slots

TIME_OPTIONS = _generate_time_options()


# ------------ Prepare Events ------------
def _prepare_events():
    events = []
    for i, b in enumerate(st.session_state.bookings):
        events.append({
            "id": str(i),
            "title": f"{b['purpose']} ({b['dept']})",
            "start": b["start"].isoformat(),
            "end": b["end"].isoformat(),
            "color": "#7A42FF",
        })
    return events


# ---------------- MAIN PAGE ----------------
def render_booking_page():

    # Init
    if "bookings" not in st.session_state:
        st.session_state.bookings = []

    if "edit_index" not in st.session_state:
        st.session_state.edit_index = None


    # ---------------- HEADER BOX ----------------
    st.markdown(f"""
    <style>
        header[data-testid="stHeader"] {{ display:none !important; }}

        .block-container {{
            padding-top:0rem !important;
        }}

        .header-box {{
            background:{HEADER_GRADIENT};
            padding:26px 30px;
            margin:-1rem -1rem 2rem -1rem;
            border-radius:18px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            box-shadow:0 6px 16px rgba(0,0,0,0.18);
        }}

        .header-title {{
            font-size:30px;
            font-weight:800;
            color:#fff;
            font-family:'Inter',sans-serif;
            letter-spacing:1px;
        }}

        .header-logo {{
            height:50px;
        }}

        /* Form Box */
        .form-card {{
            background:{HEADER_GRADIENT};
            padding:18px;
            border-radius:18px;
            box-shadow:0 3px 10px rgba(0,0,0,0.10);
        }}

        .form-title {{
            font-size:22px;
            font-weight:700;
            color:white;
            margin-bottom:12px;
        }}

        .white-box {{
            background:white;
            padding:14px;
            border-radius:12px;
            margin-bottom:12px;
        }}

        .form-btn {{
            width:100%;
            background:white!important;
            color:#50309D!important;
            font-weight:700!important;
            border:none!important;
            border-radius:8px!important;
            padding:10px!important;
            box-shadow:0 2px 8px rgba(0,0,0,0.12)!important;
        }}
    </style>

    <div class="header-box">
        <button onclick="window.location.reload();" style="background:rgba(255,255,255,0.2);border:none;color:white;padding:6px 14px;border-radius:8px;font-size:15px;cursor:pointer" id="back_btn">←</button>
        <div class="header-title">Conference Booking</div>
        <img src="{LOGO_URL}" class="header-logo">
    </div>
    """, unsafe_allow_html=True)


    # 🟣 Layout
    col_cal, col_form = st.columns([2,1], gap="large")


    # ---------------- CALENDAR ----------------
    with col_cal:
        MIN_TIME = f"{WORKING_HOUR_START:02}:{WORKING_MINUTE_START:02}:00"
        MAX_TIME = f"{WORKING_HOUR_END:02}:{WORKING_MINUTE_END:02}:00"

        calendar(
            events=_prepare_events(),
            options={
                "initialView":"timeGridDay",
                "slotDuration":"00:30:00",
                "slotMinTime":MIN_TIME,
                "slotMaxTime":MAX_TIME,
                "height":720,
                "headerToolbar":{
                    "left":"today prev,next",
                    "center":"title",
                    "right":"timeGridDay,timeGridWeek",
                },
            },
            key="calendar_view",
        )

        st.write("## 🗂 Bookings Today")
        _draw_table()


    # ---------------- BOOKING FORM ----------------
    with col_form:
        _draw_form()


# ---------------- FORM UI ----------------
def _draw_form():

    editing = st.session_state.edit_index is not None

    with st.container():
        st.markdown("<div class='form-card'>", unsafe_allow_html=True)
        
        if editing:
            st.markdown("<div class='form-title'>✏️ Edit Booking</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='form-title'>📝 Book a Slot</div>", unsafe_allow_html=True)

        if editing:
            b = st.session_state.bookings[st.session_state.edit_index]
            default_date = b['start'].date()
            default_start = b['start'].strftime("%I:%M %p")
            default_end = b['end'].strftime("%I:%M %p")
            default_dept = b['dept']
            default_purpose = b['purpose']
        else:
            default_date = datetime.today().date()
            default_start = "Select"
            default_end = "Select"
            default_dept = "Select"
            default_purpose = "Select"

        with st.form("booking_form"):
            with st.container():
                booking_date = st.date_input("Date", default_date)
                start_str = st.selectbox("Start Time", TIME_OPTIONS,
                                        index=TIME_OPTIONS.index(default_start))
                end_str = st.selectbox("End Time", TIME_OPTIONS,
                                        index=TIME_OPTIONS.index(default_end))
                dept = st.selectbox("Department", DEPARTMENT_OPTIONS,
                                        index=DEPARTMENT_OPTIONS.index(default_dept))
                purpose = st.selectbox("Purpose", PURPOSE_OPTIONS,
                                        index=PURPOSE_OPTIONS.index(default_purpose))

            submitted = st.form_submit_button("Save Slot", type="primary", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        if submitted:
            _save_booking(booking_date, start_str, end_str, dept, purpose)


# ---------------- SAVE ----------------
def _save_booking(booking_date, start_str, end_str, dept, purpose):
    start_time = datetime.strptime(start_str, "%I:%M %p").time()
    end_time = datetime.strptime(end_str, "%I:%M %p").time()

    start_dt = datetime.combine(booking_date, start_time)
    end_dt = datetime.combine(booking_date, end_time)

    if st.session_state.edit_index is not None:
        st.session_state.bookings[st.session_state.edit_index] = {
            "start":start_dt,
            "end":end_dt,
            "dept":dept,
            "purpose":purpose,
        }
        st.session_state.edit_index = None
        st.success("Booking Updated")
    else:
        st.session_state.bookings.append({
            "start":start_dt,
            "end":end_dt,
            "dept":dept,
            "purpose":purpose,
        })
        st.success("Booking Confirmed")

    st.rerun()


# ---------------- TABLE ----------------
def _draw_table():
    if not st.session_state.bookings:
        st.info("No bookings today.")
        return

    import pandas as pd

    rows = []
    for i, b in enumerate(st.session_state.bookings):
        rows.append({
            "Department": b["dept"],
            "Purpose": b["purpose"],
            "Start": b["start"].strftime("%I:%M %p"),
            "End": b["end"].strftime("%I:%M %p"),
        })
    df = pd.DataFrame(rows)

    st.dataframe(df, hide_index=True, use_container_width=True)

    for i, b in enumerate(st.session_state.bookings):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ Edit", key=f"edit_{i}"):
                st.session_state.edit_index = i
                st.rerun()
        with col2:
            if st.button("🗑 Cancel", key=f"del_{i}"):
                st.session_state.bookings.pop(i)
                st.success("Booking Cancelled")
                st.rerun()
