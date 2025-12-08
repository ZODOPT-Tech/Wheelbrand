import streamlit as st
from datetime import datetime, timedelta, time
from streamlit_calendar import calendar

# ------------------- GLOBAL SETTINGS -------------------
HEADER_GRADIENT = "linear-gradient(90deg, #50309D 0%, #7A42FF 100%)"

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


# ------------------- UTILITIES -------------------
def _generate_time_options():
    slots = ["Select"]
    start_dt = datetime(1, 1, 1, WORKING_HOUR_START, WORKING_MINUTE_START)
    end_dt = datetime(1, 1, 1, WORKING_HOUR_END, WORKING_MINUTE_END)

    while start_dt <= end_dt:
        slots.append(start_dt.strftime("%I:%M %p"))
        start_dt += timedelta(minutes=30)
    return slots


TIME_OPTIONS = _generate_time_options()


def _prepare_events():
    events = []
    for i, booking in enumerate(st.session_state.bookings):
        events.append({
            "id": str(i),
            "title": f"[{booking['dept']}] {booking['purpose']}",
            "start": booking["start"].isoformat(),
            "end": booking["end"].isoformat(),
            "color": "#7A42FF",
        })
    return events


# ------------------- HEADER UI -------------------
def render_page_header():
    st.markdown(f"""
    <style>
    header[data-testid="stHeader"] {{
        display:none;
    }}

    .header-box {{
        background: {HEADER_GRADIENT};
        padding: 22px 35px;
        margin: -1rem -1rem 1.6rem -1rem;
        border-radius: 0px 0px 22px 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0px 6px 16px rgba(0,0,0,0.20);
    }}
    .header-title {{
        font-size: 30px;
        font-weight: 800;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
        letter-spacing: 1px;
    }}
    .back-btn {{
        font-size: 24px;
        font-weight: 700;
        color: #FFFFFF;
        cursor:pointer;
        padding:8px 14px;
        border-radius:10px;
    }}
    .back-btn:hover {{
        background: rgba(255,255,255,0.15);
    }}
    
    /* FORM TRANSPARENT */
    .stForm {{
        background: transparent !important;
        padding: 0 !important;
    }}

    /* Input UI */
    .stTextInput > div > input, 
    .stSelectbox div[data-baseweb="select"] input {{
        background-color: #F4F6FA !important;
        border-radius: 10px !important;
        font-size: 15px !important;
    }}
    .stDateInput input {{
        background-color: #F4F6FA !important;
        border-radius: 10px !important;
    }}
    .stSelectbox div[data-baseweb="select"] {{
        background-color:#F4F6FA !important;
        border-radius:10px !important;
        border:1px solid #E5E7EB !important;
        height:48px !important;
    }}

    /* Save Button */
    .save-button > button {{
        width:100% !important;
        background:{HEADER_GRADIENT} !important;
        border:none !important;
        border-radius:10px !important;
        height:48px !important;
        font-size:18px !important;
        font-weight:700 !important;
        color:white !important;
        box-shadow:0 3px 10px rgba(0,0,0,0.08);
        transition:0.2s ease;
    }}
    .save-button > button:hover {{
        opacity:0.92;
        transform:translateY(-1px);
    }}
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([8, 1])
    with col1:
        st.markdown('<div class="header-title">CONFERENCE BOOKING</div>', unsafe_allow_html=True)

    with col2:
        if st.markdown('<div class="back-btn" onclick="window.location.reload()">←</div>', unsafe_allow_html=True):
            pass
        if st.button(" ", help="Back", key="back_btn_style"):
            st.session_state['current_page'] = 'conference_dashboard'
            st.rerun()


# ------------------- MAIN PAGE -------------------
def render_booking_page():
    # Sessions
    if "bookings" not in st.session_state:
        st.session_state.bookings = []
    if "edit_index" not in st.session_state:
        st.session_state.edit_index = None

    render_page_header()

    col_calendar, col_form = st.columns([2, 1])

    # ---------- CALENDAR ----------
    with col_calendar:
        st.subheader("📅 Schedule View")

        min_time = f"{WORKING_HOUR_START:02}:{WORKING_MINUTE_START:02}:00"
        max_time = f"{WORKING_HOUR_END:02}:{WORKING_MINUTE_END:02}:00"

        calendar(
            events=_prepare_events(),
            options={
                "initialView": "timeGridDay",
                "slotDuration": "00:30:00",
                "slotMinTime": min_time,
                "slotMaxTime": max_time,
                "height": 700,
                "headerToolbar": {
                    "left": "today prev,next",
                    "center": "title",
                    "right": "timeGridDay,timeGridWeek",
                },
            },
            key="calendar",
        )

        st.subheader("📌 Your Bookings")
        _draw_booking_table()

    # ---------- FORM ----------
    with col_form:
        _booking_form()


# ------------------- BOOKING FORM -------------------
def _booking_form():
    edit = st.session_state.edit_index is not None
    st.subheader("✏️ Edit Booking" if edit else "📝 Book a Slot")

    if edit:
        b = st.session_state.bookings[edit]
        default_date = b["start"].date()
        default_start = b["start"].strftime("%I:%M %p")
        default_end = b["end"].strftime("%I:%M %p")
        default_dept = b["dept"]
        default_purpose = b["purpose"]
    else:
        default_date = datetime.today().date()
        default_start = "Select"
        default_end = "Select"
        default_dept = "Select"
        default_purpose = "Select"

    with st.form("booking_form"):
        booking_date = st.date_input("Date", default_date)
        start_time = st.selectbox("Start Time", TIME_OPTIONS, index=TIME_OPTIONS.index(default_start))
        end_time = st.selectbox("End Time", TIME_OPTIONS, index=TIME_OPTIONS.index(default_end))
        dept = st.selectbox("Department", DEPARTMENT_OPTIONS, index=DEPARTMENT_OPTIONS.index(default_dept))
        purpose = st.selectbox("Purpose", PURPOSE_OPTIONS, index=PURPOSE_OPTIONS.index(default_purpose))

        save = st.form_submit_button("Save Slot", use_container_width=True)

        if save:
            _save_booking(booking_date, start_time, end_time, dept, purpose)
            st.rerun()


# ------------------- SAVE BOOKING -------------------
def _save_booking(booking_date, start_str, end_str, dept, purpose):
    if start_str == "Select" or end_str == "Select":
        st.error("Select valid start and end timing.")
        return

    if dept == "Select" or purpose == "Select":
        st.error("Select Department and Purpose")
        return

    start_time = datetime.strptime(start_str, "%I:%M %p").time()
    end_time = datetime.strptime(end_str, "%I:%M %p").time()
    start_dt = datetime.combine(booking_date, start_time)
    end_dt = datetime.combine(booking_date, end_time)

    if end_dt <= start_dt:
        st.error("End time must be after start time.")
        return

    min_dt = datetime.combine(booking_date, time(WORKING_HOUR_START, WORKING_MINUTE_START))
    max_dt = datetime.combine(booking_date, time(WORKING_HOUR_END, WORKING_MINUTE_END))

    if start_dt < min_dt or end_dt > max_dt:
        st.error("Booking must be within office hours (9:30 AM - 7:00 PM).")
        return

    for i, b in enumerate(st.session_state.bookings):
        if st.session_state.edit_index is not None and i == st.session_state.edit_index:
            continue
        if b["start"] < end_dt and b["end"] > start_dt:
            st.error("This slot is already booked.")
            return

    if st.session_state.edit_index is not None:
        st.session_state.bookings[st.session_state.edit_index] = {
            "start": start_dt,
            "end": end_dt,
            "dept": dept,
            "purpose": purpose
        }
        st.session_state.edit_index = None
    else:
        st.session_state.bookings.append({
            "start": start_dt,
            "end": end_dt,
            "dept": dept,
            "purpose": purpose
        })


# ------------------- BOOKING TABLE -------------------
def _draw_booking_table():
    if not st.session_state.bookings:
        st.info("No bookings yet.")
        return

    for i, b in enumerate(st.session_state.bookings):
        cols = st.columns([4, 2, 2, 1, 1])
        with cols[0]:
            st.write(f"**{b['purpose']}**  ({b['dept']})")
        with cols[1]:
            st.write(b["start"].strftime("%d-%m %H:%M"))
        with cols[2]:
            st.write(b["end"].strftime("%d-%m %H:%M"))
        with cols[3]:
            if st.button("Edit", key=f"edit_{i}"):
                st.session_state.edit_index = i
                st.rerun()
        with cols[4]:
            if st.button("❌", key=f"del_{i}"):
                st.session_state.bookings.pop(i)
                st.rerun()
