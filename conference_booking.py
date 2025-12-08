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
            "color": "#7A42FF",
        })
    return events


# ------------ MAIN FUNCTION ------------
def render_booking_page():
    
    # Initialise bookings
    if "bookings" not in st.session_state:
        st.session_state.bookings = []
        
    if "edit_index" not in st.session_state:
        st.session_state.edit_index = None

    # ---- HEADER ----
    cols = st.columns([6, 1])
    with cols[0]:
        st.title("🗓 Conference Room Booking")

    with cols[1]:
        # Back button
        if st.button("←", help="Back"):
            st.session_state['current_page'] = 'conference_dashboard'
            st.rerun()

    st.write("Book the conference room using calendar and form, or modify existing bookings.")

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

        st.subheader("🗂 Bookings Today")
        _draw_bookings_table()

    # ---- BOOKING FORM SECTION ----
    with col_form:
        _draw_booking_form()


# ---------------- FORM UI ----------------
def _draw_booking_form():

    editing = st.session_state.edit_index is not None
    form_title = "✏️ Update Booking" if editing else "📝 Book a Slot"
    st.subheader(form_title)

    # if editing, load existing data
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
        booking_date = st.date_input("Date", default_date)
        start_str = st.selectbox("Start Time", TIME_OPTIONS, index=TIME_OPTIONS.index(default_start))
        end_str = st.selectbox("End Time", TIME_OPTIONS, index=TIME_OPTIONS.index(default_end))

        dept = st.selectbox("Department", DEPARTMENT_OPTIONS, index=DEPARTMENT_OPTIONS.index(default_dept))
        purpose = st.selectbox("Purpose", PURPOSE_OPTIONS, index=PURPOSE_OPTIONS.index(default_purpose))

        submitted = st.form_submit_button("Save Booking")

        if submitted:
            _save_booking(booking_date, start_str, end_str, dept, purpose)


# ---------------- SAVE BOOKING ----------------
def _save_booking(booking_date, start_str, end_str, dept, purpose):
    if start_str == "Select" or end_str == "Select":
        st.error("Select valid start and end time.")
        st.stop()

    if dept == "Select" or purpose == "Select":
        st.error("Select Department and Purpose.")
        st.stop()

    start_time = datetime.strptime(start_str, "%I:%M %p").time()
    end_time = datetime.strptime(end_str, "%I:%M %p").time()

    start_dt = datetime.combine(booking_date, start_time)
    end_dt = datetime.combine(booking_date, end_time)

    if end_dt <= start_dt:
        st.error("End time must be after start time.")
        st.stop()

    min_dt = datetime.combine(booking_date, time(WORKING_HOUR_START, WORKING_MINUTE_START))
    max_dt = datetime.combine(booking_date, time(WORKING_HOUR_END, WORKING_MINUTE_END))

    if start_dt < min_dt or end_dt > max_dt:
        st.error("Booking must be within 9:30 AM - 7 PM.")
        st.stop()

    # Overlap (skip current editing index)
    for i, b in enumerate(st.session_state.bookings):
        if st.session_state.edit_index is not None and i == st.session_state.edit_index:
            continue
        if b["start"] < end_dt and b["end"] > start_dt:
            st.error("This slot is already booked.")
            st.stop()

    # Save result
    if st.session_state.edit_index is not None:
        # Update existing booking
        st.session_state.bookings[st.session_state.edit_index] = {
            "start": start_dt,
            "end": end_dt,
            "dept": dept,
            "purpose": purpose,
        }
        st.session_state.edit_index = None
        st.success("Booking Updated")
    else:
        # Create new
        st.session_state.bookings.append({
            "start": start_dt,
            "end": end_dt,
            "dept": dept,
            "purpose": purpose,
        })
        st.success("Booking Confirmed")

    st.rerun()


# ---------------- TABLE UI ----------------
def _draw_bookings_table():
    if not st.session_state.bookings:
        st.info("No bookings.")
        return

    import pandas as pd

    rows = []
    for i, b in enumerate(st.session_state.bookings):
        rows.append({
            "Department": b["dept"],
            "Purpose": b["purpose"],
            "Start": b["start"].strftime("%I:%M %p"),
            "End": b["end"].strftime("%I:%M %p"),
            "Actions": i,
        })

    df = pd.DataFrame(rows)

    st.dataframe(df, use_container_width=True, hide_index=True)

    # --- Action Buttons ---
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
