import streamlit as st
from datetime import datetime, timedelta, time
from streamlit_calendar import calendar

# ---------------- SETTINGS ----------------
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
    start_dt = datetime(1, 1, 1, WORKING_HOUR_START, WORKING_MINUTE_START)
    end_dt = datetime(1, 1, 1, WORKING_HOUR_END, WORKING_MINUTE_END)

    while start_dt <= end_dt:
        slots.append(start_dt.strftime("%I:%M %p"))
        start_dt += timedelta(minutes=30)
    return slots

TIME_OPTIONS = _generate_time_options()


# ------------ Generate Calendar Events ------------
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


# ------------ MAIN PAGE ------------
def render_booking_page():
    
    # Initialize bookings list
    if "bookings" not in st.session_state:
        st.session_state.bookings = []

    st.title("🗓 Conference Room Booking")
    st.write("Book the conference room using the calendar and form.")

    col_calendar, col_form = st.columns([2, 1])

    # ---- CALENDAR SECTION ----
    with col_calendar:
        st.subheader("📅 Schedule View")

        MIN_TIME = f"{WORKING_HOUR_START:02}:{WORKING_MINUTE_START:02}:00"
        MAX_TIME = f"{WORKING_HOUR_END:02}:{WORKING_MINUTE_END:02}:00"

        calendar(
            events=_prepare_events(),
            options={
                "initialView": "timeGridDay",
                "slotDuration": "00:30:00",
                "slotMinTime": MIN_TIME,
                "slotMaxTime": MAX_TIME,
                "height": 700,
                "headerToolbar": {
                    "left": "today prev,next",
                    "center": "title",
                    "right": "timeGridDay,timeGridWeek",
                },
            },
            key="calendar",
        )

    # ---- BOOKING FORM SECTION ----
    with col_form:
        st.subheader("📝 Book a Slot")
        with st.form("booking_form"):
            booking_date = st.date_input("Date", datetime.today().date())
            start_str = st.selectbox("Start Time", TIME_OPTIONS)
            end_str = st.selectbox("End Time", TIME_OPTIONS)

            dept = st.selectbox("Department", DEPARTMENT_OPTIONS)
            purpose = st.selectbox("Purpose", PURPOSE_OPTIONS)

            submitted = st.form_submit_button("Confirm Booking")

            if submitted:
                # Validations
                if start_str == "Select" or end_str == "Select":
                    st.error("Select valid start & end time.")
                    st.stop()

                if dept == "Select":
                    st.error("Select Department.")
                    st.stop()

                if purpose == "Select":
                    st.error("Select Purpose.")
                    st.stop()

                start_time = datetime.strptime(start_str, "%I:%M %p").time()
                end_time = datetime.strptime(end_str, "%I:%M %p").time()

                start_dt = datetime.combine(booking_date, start_time)
                end_dt = datetime.combine(booking_date, end_time)

                # Check order
                if end_dt <= start_dt:
                    st.error("End time must be after start time.")
                    st.stop()

                # Working hour limits
                min_dt = datetime.combine(booking_date, time(WORKING_HOUR_START, WORKING_MINUTE_START))
                max_dt = datetime.combine(booking_date, time(WORKING_HOUR_END, WORKING_MINUTE_END))

                if start_dt < min_dt or end_dt > max_dt:
                    st.error("Booking must be within working hours (9:30 AM - 7:00 PM).")
                    st.stop()

                # Overlap check
                for b in st.session_state.bookings:
                    if b["start"] < end_dt and b["end"] > start_dt:
                        st.error("This slot is already booked.")
                        st.stop()

                # Save booking
                st.session_state.bookings.append({
                    "start": start_dt,
                    "end": end_dt,
                    "dept": dept,
                    "purpose": purpose
                })

                st.success("Booking Confirmed!")
                st.rerun()
