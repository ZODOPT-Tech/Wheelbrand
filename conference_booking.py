import streamlit as st
from datetime import datetime, timedelta, time
from streamlit_calendar import calendar

# ---------------- SETTINGS ----------------
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
    "IT",
]

PURPOSE_OPTIONS = [
    "Select",
    "Client Visit",
    "Internal Meeting",
    "HOD Meeting",
    "Inductions",
    "Training",
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
        events.append(
            {
                "id": str(i),
                "title": f"{b['purpose']} ({b['dept']})",
                "start": b["start"].isoformat(),
                "end": b["end"].isoformat(),
                "color": "#7A42FF",
            }
        )
    return events


# ------------ MAIN PAGE ------------
def render_booking_page():
    # --- init state ---
    if "bookings" not in st.session_state:
        st.session_state.bookings = []
    if "edit_index" not in st.session_state:
        st.session_state.edit_index = None

    # --- GLOBAL CSS ---
    st.markdown(
        f"""
    <style>
        /* Remove default Streamlit header and pull content up */
        header[data-testid="stHeader"] {{
            display: none !important;
        }}
        .block-container {{
            padding-top: 0rem !important;
        }}

        /* HEADER BAR */
        .conf-header {{
            background: {HEADER_GRADIENT};
            padding: 22px 32px;
            margin: 0 -1rem 1.5rem -1rem;
            border-radius: 0 0 18px 18px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.18);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .conf-title {{
            font-size: 28px;
            font-weight: 800;
            color: #fff;
            font-family: "Inter", sans-serif;
            letter-spacing: 1px;
        }}

        /* Make the form background transparent */
        .stForm {{
            background: transparent !important;
            padding: 0 !important;
        }}

        /* Inputs */
        .stDateInput input,
        .stTextInput > div > input,
        .stSelectbox div[data-baseweb="select"] {{
            background-color: #F4F6FA !important;
            border-radius: 10px !important;
            border: 1px solid #E5E7EB !important;
            font-size: 15px !important;
        }}

        /* Gradient submit button inside the form */
        .stForm button[type="submit"] {{
            background: {HEADER_GRADIENT} !important;
            color: #fff !important;
            border: none !important;
            border-radius: 10px !important;
            font-size: 16px !important;
            font-weight: 700 !important;
            height: 48px !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
        }}
        .stForm button[type="submit"]:hover {{
            opacity: 0.95;
            transform: translateY(-1px);
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    # --- HEADER BAR (title + back button) ---
    header_left, header_right = st.columns([8, 1])
    with header_left:
        st.markdown(
            '<div class="conf-header"><div class="conf-title">CONFERENCE BOOKING</div></div>',
            unsafe_allow_html=True,
        )
    with header_right:
        # back button top-right (outside gradient but visually close)
        if st.button("←", help="Back to dashboard"):
            st.session_state["current_page"] = "conference_dashboard"
            st.rerun()

    # --- MAIN LAYOUT: Calendar + Form ---
    col_calendar, col_form = st.columns([2, 1])

    # ---- CALENDAR SECTION ----
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
                "height": 650,
                "headerToolbar": {
                    "left": "today prev,next",
                    "center": "title",
                    "right": "timeGridDay,timeGridWeek",
                },
            },
            key="full_calendar",
        )

        st.subheader("📌 Bookings")
        _draw_bookings_table()

    # ---- BOOKING FORM SECTION ----
    with col_form:
        _render_booking_form()


# ------------ FORM RENDERING ------------
def _render_booking_form():
    editing = st.session_state.edit_index is not None

    st.subheader("✏️ Edit Booking" if editing else "📝 Book a Slot")

    if editing:
        b = st.session_state.bookings[st.session_state.edit_index]
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
        start_str = st.selectbox(
            "Start Time", TIME_OPTIONS, index=TIME_OPTIONS.index(default_start)
        )
        end_str = st.selectbox(
            "End Time", TIME_OPTIONS, index=TIME_OPTIONS.index(default_end)
        )
        dept = st.selectbox(
            "Department",
            DEPARTMENT_OPTIONS,
            index=DEPARTMENT_OPTIONS.index(default_dept),
        )
        purpose = st.selectbox(
            "Purpose",
            PURPOSE_OPTIONS,
            index=PURPOSE_OPTIONS.index(default_purpose),
        )

        submitted = st.form_submit_button("Save Slot", use_container_width=True)

    if submitted:
        _save_booking(booking_date, start_str, end_str, dept, purpose)


# ------------ SAVE / UPDATE BOOKING ------------
def _save_booking(booking_date, start_str, end_str, dept, purpose):
    if start_str == "Select" or end_str == "Select":
        st.error("Please select valid start & end time.")
        return
    if dept == "Select":
        st.error("Please select a Department.")
        return
    if purpose == "Select":
        st.error("Please select a Purpose.")
        return

    start_time = datetime.strptime(start_str, "%I:%M %p").time()
    end_time = datetime.strptime(end_str, "%I:%M %p").time()

    start_dt = datetime.combine(booking_date, start_time)
    end_dt = datetime.combine(booking_date, end_time)

    if end_dt <= start_dt:
        st.error("End time must be after start time.")
        return

    min_dt = datetime.combine(
        booking_date, time(WORKING_HOUR_START, WORKING_MINUTE_START)
    )
    max_dt = datetime.combine(
        booking_date, time(WORKING_HOUR_END, WORKING_MINUTE_END)
    )

    if start_dt < min_dt or end_dt > max_dt:
        st.error("Booking must be within working hours (9:30 AM - 7:00 PM).")
        return

    # Overlap check (ignore currently edited slot)
    for i, b in enumerate(st.session_state.bookings):
        if st.session_state.edit_index is not None and i == st.session_state.edit_index:
            continue
        if b["start"] < end_dt and b["end"] > start_dt:
            st.error("This slot overlaps with an existing booking.")
            return

    # Save / update
    if st.session_state.edit_index is not None:
        st.session_state.bookings[st.session_state.edit_index] = {
            "start": start_dt,
            "end": end_dt,
            "dept": dept,
            "purpose": purpose,
        }
        st.session_state.edit_index = None
        st.success("Booking updated.")
    else:
        st.session_state.bookings.append(
            {
                "start": start_dt,
                "end": end_dt,
                "dept": dept,
                "purpose": purpose,
            }
        )
        st.success("Booking confirmed.")

    st.rerun()


# ------------ TABLE OF BOOKINGS ------------
def _draw_bookings_table():
    if not st.session_state.bookings:
        st.info("No bookings yet.")
        return

    # Simple list with Edit / Cancel buttons
    for i, b in enumerate(sorted(st.session_state.bookings, key=lambda x: x["start"])):
        c1, c2, c3, c4 = st.columns([4, 3, 2, 2])

        with c1:
            st.write(f"**{b['purpose']}**  · {b['dept']}")
        with c2:
            st.write(
                f"{b['start'].strftime('%d-%m-%Y %I:%M %p')} → {b['end'].strftime('%I:%M %p')}"
            )
        with c3:
            if st.button("Edit", key=f"edit_{i}"):
                st.session_state.edit_index = i
                st.rerun()
        with c4:
            if st.button("Cancel", key=f"del_{i}"):
                st.session_state.bookings.pop(i)
                st.success("Booking cancelled.")
                st.rerun()
