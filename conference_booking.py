import streamlit as st
from datetime import datetime, timedelta, time
from streamlit_calendar import calendar
from main import get_fast_connection  # <-- Use your existing DB connection

# ---------------- GLOBAL SETTINGS ----------------
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"

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
def _generate_time_options(selected_date):
    """Disable past slots if today."""
    slots = ["Select"]
    now = datetime.now()
    today = now.date()

    start_dt = datetime(1, 1, 1, WORKING_HOUR_START, WORKING_MINUTE_START)
    end_dt = datetime(1, 1, 1, WORKING_HOUR_END, WORKING_MINUTE_END)

    while start_dt <= end_dt:
        label = start_dt.strftime("%I:%M %p")

        if selected_date == today:
            slot_time_today = datetime.combine(today, start_dt.time())
            if slot_time_today <= now:
                label += " (Unavailable)"

        slots.append(label)
        start_dt += timedelta(minutes=30)
    return slots


# ------------ Prepare Calendar Events ------------
def _prepare_events():
    events = []
    for i, b in enumerate(st.session_state.bookings):
        events.append({
            "id": str(i),
            "title": f"{b['purpose']} ({b['dept']})",
            "start": b["start"].isoformat(),
            "end": b["end"].isoformat(),
            "color": "#ff4d4d",
        })
    return events


# ------------ Save Booking (DB + Local State) ------------
def _save_booking(date, s, e, dept, purpose):
    now = datetime.now()

    # Remove unavailable suffix
    s = s.replace(" (Unavailable)", "")
    e = e.replace(" (Unavailable)", "")

    if s == "Select" or e == "Select":
        st.error("Select valid start and end time.")
        return

    if "(Unavailable)" in s or "(Unavailable)" in e:
        st.error("Cannot book past slots.")
        return

    if dept == "Select":
        st.error("Select department.")
        return

    if purpose == "Select":
        st.error("Select purpose.")
        return

    start = datetime.combine(date, datetime.strptime(s, "%I:%M %p").time())
    end = datetime.combine(date, datetime.strptime(e, "%I:%M %p").time())

    if date < now.date():
        st.error("Cannot book past dates.")
        return

    if date == now.date() and start <= now:
        st.error("Cannot book past time.")
        return

    if end <= start:
        st.error("End time should be after start.")
        return

    # Work hours limit check
    min_dt = datetime.combine(date, time(WORKING_HOUR_START, WORKING_MINUTE_START))
    max_dt = datetime.combine(date, time(WORKING_HOUR_END, WORKING_MINUTE_END))

    if start < min_dt or end > max_dt:
        st.error("Booking must be between 9:30 AM to 7:00 PM.")
        return

    # Overlap validation
    for b in st.session_state.bookings:
        if b["start"] < end and b["end"] > start:
            st.error("Slot already booked.")
            return

    # Save in DB
    try:
        conn = get_fast_connection()
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO conference_bookings (user_id, department, purpose, start_time, end_time)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (
            st.session_state.get("user_id"),
            dept,
            purpose,
            start,
            end
        ))
        conn.commit()
    except Exception as e:
        st.error("Database Error")
        st.write(e)
        return

    # Save to local UI state for calendar refresh
    st.session_state.bookings.append({
        "start": start,
        "end": end,
        "dept": dept,
        "purpose": purpose
    })

    st.success("Booking Successful 🎉")
    st.experimental_rerun()


# ------------ Page Header ------------
def _render_header():
    st.markdown(f"""
    <style>
    header[data-testid="stHeader"] {{
        display: none;
    }}
    .header-box {{
        background: {HEADER_GRADIENT};
        padding: 18px 26px;
        margin: -1rem -1rem 1.4rem -1rem;
        border-radius: 0 0 20px 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 6px 16px rgba(0,0,0,0.18);
    }}
    .back-btn {{
        background: rgba(255,255,255,0.22);
        padding: 6px 18px;
        border-radius: 8px;
        color: white;
        font-weight: 700;
        border: 1px solid rgba(255,255,255,0.4);
        cursor:pointer;
    }}
    .title-text {{
        font-size: 26px;
        font-weight: 800;
        color: white;
    }}
    .logo-img {{
        height: 40px;
    }}
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,6,1])
    with col1:
        if st.button("←", key="back_btn"):
            st.session_state['current_page'] = 'conference_dashboard'
            st.rerun()
    with col2:
        st.markdown("<div class='title-text' style='text-align:center;'>Conference Booking</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<img src='{LOGO_URL}' class='logo-img'>", unsafe_allow_html=True)


# ------------ MAIN PAGE RENDER ------------
def render_booking_page():
    if "bookings" not in st.session_state:
        st.session_state.bookings = []

    _render_header()

    col_calendar, col_form = st.columns([2, 1])

    # ===== Calendar =====
    with col_calendar:
        st.subheader("📅 Schedule View")

        calendar(
            events=_prepare_events(),
            options={
                "initialView": "timeGridDay",
                "slotDuration": "00:30:00",
                "slotMinTime": f"{WORKING_HOUR_START:02}:{WORKING_MINUTE_START:02}:00",
                "slotMaxTime": f"{WORKING_HOUR_END:02}:{WORKING_MINUTE_END:02}:00",
                "height": 700,
                "headerToolbar": {
                    "left": "today prev,next",
                    "center": "title",
                    "right": "timeGridDay,timeGridWeek",
                },
            },
            key="calendar",
        )

    # ===== Booking Form =====
    with col_form:
        st.subheader("📝 Book a Slot")

        today = datetime.now().date()
        booking_date = st.date_input("Date", today)

        start_time_ops = _generate_time_options(booking_date)
        end_time_ops = _generate_time_options(booking_date)

        start_str = st.selectbox("Start Time", start_time_ops)
        end_str = st.selectbox("End Time", end_time_ops)

        dept = st.selectbox("Department", DEPARTMENT_OPTIONS)
        purpose = st.selectbox("Purpose", PURPOSE_OPTIONS)

        if st.button("Save Slot", use_container_width=True):
            _save_booking(booking_date, start_str, end_str, dept, purpose)
