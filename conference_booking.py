import streamlit as st
from datetime import datetime, timedelta, time
from streamlit_calendar import calendar

# ================== CONFIG ====================
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D 0%, #7A42FF 100%)"

WORKING_HOUR_START = 9
WORKING_MINUTE_START = 30
WORKING_HOUR_END = 19
WORKING_MINUTE_END = 0

DEPARTMENT_OPTIONS = [
    "Select", "Sales", "HR", "Finance",
    "Delivery/Tech", "Digital Marketing", "IT"
]

PURPOSE_OPTIONS = [
    "Select", "Client Visit", "Internal Meeting",
    "HOD Meeting", "Inductions", "Training"
]


# -------- TIME SLOTS --------
def _generate_time_options():
    slots = ["Select"]
    start_dt = datetime(1,1,1,WORKING_HOUR_START,WORKING_MINUTE_START)
    end_dt = datetime(1,1,1,WORKING_HOUR_END,WORKING_MINUTE_END)
    while start_dt <= end_dt:
        slots.append(start_dt.strftime("%I:%M %p"))
        start_dt += timedelta(minutes=30)
    return slots

TIME_OPTIONS = _generate_time_options()


# -------- CALENDAR EVENTS --------
def _prepare_events():
    events = []
    for i, b in enumerate(st.session_state.bookings):
        events.append({
            "id": str(i),
            "title": f"{b['purpose']} ({b['dept']})",
            "start": b["start"].isoformat(),
            "end": b["end"].isoformat(),
            "color": "#7A42FF"
        })
    return events


# -------- HEADER UI --------
def render_page_header():
    st.markdown(f"""
    <style>
        header[data-testid="stHeader"] {{
            display:none;
        }}
        .app-header {{
            background:{HEADER_GRADIENT};
            padding:18px 28px;
            margin:-1rem -1rem 1.5rem -1rem;
            border-radius:0 0 22px 22px;
            box-shadow:0 6px 16px rgba(0,0,0,0.20);
            display:flex;
            align-items:center;
            justify-content:space-between;
        }}
        .header-left {{
            display:flex;
            align-items:center;
            gap:14px;
        }}
        .back-btn {{
            background:rgba(255,255,255,0.18);
            padding:6px 14px;
            border-radius:8px;
            font-size:18px;
            color:#fff;
            font-weight:700;
            cursor:pointer;
            border:1px solid rgba(255,255,255,0.4);
        }}
        .title-text {{
            font-size:26px;
            font-weight:800;
            color:white;
            font-family:'Inter',sans-serif;
        }}
        .logo-img {{
            height:38px;
        }}

        /* Input Styling */
        .stForm {{
            background:transparent !important;
        }}
        .stDateInput input, .stTextInput input,
        .stSelectbox div[data-baseweb="select"] {{
            background:#F5F7FB !important;
            border-radius:10px!important;
            border:1px solid #E5E7EB!important;
        }}

        /* Save Button = Gradient */
        .stForm button[type="submit"] {{
            background:{HEADER_GRADIENT}!important;
            color:white!important;
            font-weight:700!important;
            height:48px!important;
            border:none!important;
            border-radius:10px!important;
            box-shadow:0 2px 8px rgba(0,0,0,0.15)!important;
        }}
        .stForm button[type="submit"]:hover {{
            opacity:0.92;
            transform:translateY(-1px);
        }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="app-header">
        <div class="header-left">
            <button class="back-btn" onclick="window.location.reload()">←</button>
            <div class="title-text">CONFERENCE BOOKING</div>
        </div>
        <img class="logo-img" src="{LOGO_URL}"/>
    </div>
    """, unsafe_allow_html=True)


# -------- MAIN PAGE --------
def render_booking_page():
    if "bookings" not in st.session_state:
        st.session_state.bookings = []
    if "edit_index" not in st.session_state:
        st.session_state.edit_index = None

    render_page_header()

    col_cal, col_form = st.columns([2,1])

    # ------ Calendar ------
    with col_cal:
        st.subheader("📅 Schedule View")

        min_time = f"{WORKING_HOUR_START:02}:{WORKING_MINUTE_START:02}:00"
        max_time = f"{WORKING_HOUR_END:02}:{WORKING_MINUTE_END:02}:00"

        calendar(
            events=_prepare_events(),
            options={
                "initialView":"timeGridDay",
                "slotDuration":"00:30:00",
                "slotMinTime":min_time,
                "slotMaxTime":max_time,
                "height":650,
                "headerToolbar":{
                    "left":"today prev,next",
                    "center":"title",
                    "right":"timeGridDay,timeGridWeek"
                }
            },
            key="conf_calendar"
        )

        st.subheader("📌 Bookings")
        _render_booking_table()

    # ------ Form ------
    with col_form:
        _render_form()


# -------- FORM --------
def _render_form():
    edit = st.session_state.edit_index is not None

    st.subheader("✏️ Edit Booking" if edit else "📝 Book a Slot")

    if edit:
        b = st.session_state.bookings[edit]
        date_default = b["start"].date()
        s_default = b["start"].strftime("%I:%M %p")
        e_default = b["end"].strftime("%I:%M %p")
        d_default = b["dept"]
        p_default = b["purpose"]
    else:
        date_default = datetime.today().date()
        s_default = e_default = "Select"
        d_default = p_default = "Select"

    with st.form("booking_form"):
        date = st.date_input("Date", date_default)
        start_str = st.selectbox("Start Time", TIME_OPTIONS, TIME_OPTIONS.index(s_default))
        end_str = st.selectbox("End Time", TIME_OPTIONS, TIME_OPTIONS.index(e_default))
        dept = st.selectbox("Department", DEPARTMENT_OPTIONS, DEPARTMENT_OPTIONS.index(d_default))
        purpose = st.selectbox("Purpose", PURPOSE_OPTIONS, PURPOSE_OPTIONS.index(p_default))

        submit = st.form_submit_button("Save Slot", use_container_width=True)

    if submit:
        _save(date, start_str, end_str, dept, purpose)


# -------- SAVE --------
def _save(date, s, e, dept, purpose):
    if s=="Select" or e=="Select":
        st.error("Select start/end time.")
        return
    if dept=="Select" or purpose=="Select":
        st.error("Select valid department/purpose.")
        return

    start = datetime.combine(date, datetime.strptime(s,"%I:%M %p").time())
    end = datetime.combine(date, datetime.strptime(e,"%I:%M %p").time())

    if end <= start:
        st.error("End time must be after start.")
        return

    # overlap check
    for i,b in enumerate(st.session_state.bookings):
        if st.session_state.edit_index==i: 
            continue
        if b["start"]<end and b["end"]>start:
            st.error("Slot already booked.")
            return

    if st.session_state.edit_index is not None:
        st.session_state.bookings[st.session_state.edit_index] = {
            "start":start,"end":end,"dept":dept,"purpose":purpose
        }
        st.session_state.edit_index=None
        st.success("Booking updated.")
    else:
        st.session_state.bookings.append(
            {"start":start,"end":end,"dept":dept,"purpose":purpose}
        )
        st.success("Booking created.")

    st.rerun()


# -------- TABLE --------
def _render_booking_table():
    if not st.session_state.bookings:
        st.info("No bookings yet.")
        return

    for i,b in enumerate(sorted(st.session_state.bookings,key=lambda x:x["start"])):
        c1,c2,c3,c4 = st.columns([4,3,2,2])
        with c1:
            st.write(f"**{b['purpose']}** · {b['dept']}")
        with c2:
            st.write(f"{b['start'].strftime('%d-%m %I:%M %p')} → {b['end'].strftime('%I:%M %p')}")
        with c3:
            if st.button("Edit",key=f"edit{i}"):
                st.session_state.edit_index=i
                st.rerun()
        with c4:
            if st.button("Cancel",key=f"del{i}"):
                st.session_state.bookings.pop(i)
                st.success("Booking cancelled.")
                st.rerun()
