import streamlit as st
from datetime import datetime, timedelta, time
from streamlit_calendar import calendar

# === PAGE CONFIG ===
st.set_page_config(page_title="ZODOPT MeetEase - Scheduler", layout="wide")

# --- WORKING HOURS SETTINGS ---
WORKING_HOUR_START = 9
WORKING_MINUTE_START = 30
WORKING_HOUR_END = 19
WORKING_MINUTE_END = 0

DEPARTMENT_OPTIONS = ["Select", "Sales", "HR", "Finance", "Delivery/Tech", "Digital Marketing", "IT"]
PURPOSE_OPTIONS = ["Select", "Client Visit", "Internal Meeting", "HOD Meeting", "Inductions", "Training"]

# --- Store Bookings in Session ---
if "bookings" not in st.session_state:
    st.session_state.bookings = []

# --- Create Timeslots ---
def generate_time_slots():
    slots = ["Select"]
    start_dt = datetime(1,1,1,WORKING_HOUR_START,WORKING_MINUTE_START)
    end_dt = datetime(1,1,1,WORKING_HOUR_END,WORKING_MINUTE_END)

    while start_dt <= end_dt:
        slots.append(start_dt.strftime("%I:%M %p"))
        start_dt += timedelta(minutes=30)

    return slots

TIME_OPTIONS = generate_time_slots()

# --- Calendar Events ---
def prepare_events(bookings_list):
    events = []
    for i, booking in enumerate(bookings_list):
        events.append({
            "id": str(i),
            "title": f"{booking['purpose']} ({booking['dept']})",
            "start": booking["start"].isoformat(),
            "end": booking["end"].isoformat(),
            "color": "#ff4d4d",
            "resourceId": "RoomA"
        })
    return events


# === UI ===
st.title("🗓️ ZODOPT MeetEase — Conference Room Scheduler")
st.write("Book the conference room below using the booking form.")


col_calendar, col_form = st.columns([2, 1])

# === Calendar ===
with col_calendar:
    st.subheader("📅 Schedule View")

    calendar_options = {
        "initialView": "timeGridDay",
        "slotDuration": "00:30:00",
        "slotMinTime": f"{WORKING_HOUR_START:02}:{WORKING_MINUTE_START:02}:00",
        "slotMaxTime": f"{WORKING_HOUR_END:02}:{WORKING_MINUTE_END:02}:00",
        "height": 700,
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "timeGridDay,timeGridWeek"
        },
    }

    events_data = prepare_events(st.session_state.bookings)

    calendar(
        events=events_data,
        options=calendar_options,
        key="calendar",
    )


# === Booking Form ===
with col_form:
    st.subheader("📝 Book a Slot")

    with st.form("booking_form"):
        booking_date = st.date_input("Date", datetime.today().date())
        start_time_str = st.selectbox("Start Time", options=TIME_OPTIONS)
        end_time_str = st.selectbox("End Time", options=TIME_OPTIONS)

        department = st.selectbox("Department", options=DEPARTMENT_OPTIONS)
        purpose = st.selectbox("Purpose", options=PURPOSE_OPTIONS)

        submit = st.form_submit_button("Book Slot")

        if submit:
            # Validate
            if start_time_str == "Select" or end_time_str == "Select":
                st.error("Select valid start and end times.")
                st.stop()

            if department == "Select":
                st.error("Select department.")
                st.stop()

            if purpose == "Select":
                st.error("Select meeting purpose.")
                st.stop()

            # Convert
            start_time_obj = datetime.strptime(start_time_str, "%I:%M %p").time()
            end_time_obj = datetime.strptime(end_time_str, "%I:%M %p").time()

            start_dt = datetime.combine(booking_date, start_time_obj)
            end_dt = datetime.combine(booking_date, end_time_obj)

            # Logic checks
            if end_dt <= start_dt:
                st.error("End time must be after start time.")
                st.stop()

            min_dt = datetime.combine(booking_date, time(WORKING_HOUR_START, WORKING_MINUTE_START))
            max_dt = datetime.combine(booking_date, time(WORKING_HOUR_END, WORKING_MINUTE_END))
            if start_dt < min_dt or end_dt > max_dt:
                st.error("Booking must be inside working hours (9:30 AM - 7:00 PM).")
                st.stop()

            overlap = any(b["start"] < end_dt and b["end"] > start_dt for b in st.session_state.bookings)
            if overlap:
                st.error("This slot is already booked.")
                st.stop()

            # Save booking
            st.session_state.bookings.append({
                "start": start_dt,
                "end": end_dt,
                "dept": department,
                "purpose": purpose
            })

            st.success("Booking confirmed!")
            st.rerun()
