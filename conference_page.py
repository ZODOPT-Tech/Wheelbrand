import streamlit as st
from datetime import datetime, time, timedelta
from streamlit_calendar import calendar
import uuid
import logging
import os

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONFIGURATION ---

# NOTE: Since this is running in an environment without a local file system,
# the LOGO_PATH is kept for structure but will rely on the runtime environment
# to handle or will simply show the fallback info message.
LOGO_PATH = "zodopt.png"

# UI Colors (Primary color is now the dark purple)
PRIMARY_PURPLE = "#5b46b2"
SECONDARY_GREY = "#4a4a4a"
HEADER_GRADIENT = "linear-gradient(90deg, #5b46b2 0%, #a855f7 100%)"
LOGIN_CARD_WIDTH = "450px"

# Working Hours
WORKING_HOUR_START = 9
WORKING_MINUTE_START = 30
WORKING_HOUR_END = 19
WORKING_MINUTE_END = 0

START_TIME_DEFAULT = time(WORKING_HOUR_START, WORKING_MINUTE_START)
END_TIME_DEFAULT = time(WORKING_HOUR_END, WORKING_MINUTE_END)

# Booking Constraints
MIN_ATTENDEES = 3
MAX_ATTENDEES = 10

# Dropdown Options
DEPARTMENT_OPTIONS = ["Select", "Sales", "HR", "Finance", "Delivery/Tech", "Digital Marketing", "IT"]
PURPOSE_OPTIONS = ["Select", "Client Visit", "Internal Meeting", "HOD Meeting", "Inductions", "Training"]
ATTENDEE_OPTIONS = ["Select"] + list(range(MIN_ATTENDEES, MAX_ATTENDEES + 1))


def initialize_conference_state():
    """Initializes session state specific to the Conference Room Scheduler."""
    if "bookings" not in st.session_state or not isinstance(st.session_state.bookings, list):
        st.session_state.bookings = []

    if "users" not in st.session_state:
        # Default user for testing
        st.session_state.users = {"testuser@zodopt.com": {"password": "password123", "dept": "IT"}}
    
    # Changed default page to 'login' as the primary entry point
    if "page" not in st.session_state:
        st.session_state.page = "login"
        
    if "logged_in_user" not in st.session_state:
        st.session_state.logged_in_user = None
    if "calendar_key" not in st.session_state:
        st.session_state.calendar_key = "full_weekly_calendar_0"

# --- UTILITY & UI FUNCTIONS ---

def apply_visitplan_style():
    """Applies CSS to reduce spacing, enhance professional look, and style input containers."""
    st.markdown(f"""
        <style>
        /* 1. GLOBAL SPACING REDUCTION */
        .stApp .main [data-testid="stVerticalBlock"] {{
            gap: 0.2rem;
        }}
        .stApp .main [data-testid="stForm"] {{
            padding: 0;
            margin: 0;
        }}
        .stApp [data-testid="stHorizontalBlock"] > div {{
            gap: 0.8rem;
        }}
        .stApp .main .block-container {{
            padding-top: 15px;
            padding-bottom: 15px;
            padding-left: 20px;
            padding-right: 20px;
        }}
        
        /* 2. CARD STYLING */
        .login-card-container {{
            max-width: {LOGIN_CARD_WIDTH};
            margin: 0 auto;
            margin-top: 50px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
            overflow: hidden;
            padding: 0;
        }}
        .login-header-bar {{
            background: {HEADER_GRADIENT};
            padding: 20px 25px;
        }}
        .login-header-bar h2 {{
             color: white !important;
             margin: 0 !important;
        }}
        .login-header-bar p {{
             color: #e5e5e5 !important;
             margin-top: 5px !important;
             margin-bottom: 0 !important;
             font-size: 0.9rem;
             font-weight: 300;
        }}
        .login-form-body {{
            padding: 25px;
        }}
        
        /* 3. INPUT FIELD/CONTAINER STYLING (The White Box Effect) */
        .stTextInput > div > div > input,
        .stSelectbox > div > button,
        .stDateInput > div > div > input {{
            background-color: white !important; /* Explicitly white background */
            border: 1px solid #ddd !important; /* Light grey border */
            border-radius: 6px;
            padding: 10px 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important; /* Subtle shadow */
        }}

        /* 4. TEXT SPACING */
        .login-form-body p {{
            margin-bottom: 5px !important;
            margin-top: 10px !important;
            font-size: 0.95rem;
            font-weight: 500;
        }}
        
        /* 5. PRIMARY BUTTON STYLING */
        .stButton button, [data-testid="baseButton-primary"] {{
            background-color: {PRIMARY_PURPLE} !important;
            border-color: {PRIMARY_PURPLE} !important;
            font-weight: 500;
            height: 40px;
        }}
        
        /* 6. FOOTER BUTTONS (Back to Dashboard, Sign In, Register) */
        .login-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 25px;
            border-top: 1px solid #eee;
            background-color: #fafafa;
            border-radius: 0 0 8px 8px;
        }}
        .login-footer [data-testid="stVerticalBlock"] {{
            gap: 0 !important;
        }}
        /* Secondary style for navigation buttons in the footer */
        .login-footer [data-testid="stButton"] button {{
            background-color: #ffffff !important;
            border: 1px solid #ccc !important;
            color: {SECONDARY_GREY} !important;
            padding: 5px 10px;
            height: 36px;
            font-size: 0.85rem;
            width: 100%;
        }}
        
        /* 7. Forgot Password Button (Targeted outside the form) */
        .forgot-password-container .stButton button {{
            background-color: transparent !important; /* No background */
            border: none !important; /* No border */
            color: {PRIMARY_PURPLE} !important; /* Purple text */
            text-decoration: underline;
            font-size: 0.85rem;
            height: 25px;
            padding: 0;
            text-align: right;
            justify-content: flex-end;
            margin-top: 8px; /* Alignment fix */
        }}
        .forgot-password-container .stButton button:hover {{
            color: #a855f7 !important;
        }}
        
        /* Ensure text is dark and readable everywhere else */
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText, div[data-testid="stCaption"] {{
            color: #1f1f1f !important;
            text-shadow: none;
        }}
        
        </style>
    """, unsafe_allow_html=True)


def time_slot_to_datetime(time_str, date_obj):
    """Converts a time string (e.g., '09:30 AM') and a date object into a full datetime object."""
    if time_str == "Select":
        return None
    try:
        # Streamlit time select uses %I:%M %p format (e.g., 09:30 AM)
        time_obj = datetime.strptime(time_str, "%I:%M %p").time()
        return datetime.combine(date_obj, time_obj)
    except ValueError:
        return None

def generate_time_slots(current_date):
    """Generates time slots in 15-minute intervals, filtering out past slots for the current date."""
    slots = ["Select"]
    start_time_marker = datetime(1, 1, 1, WORKING_HOUR_START, WORKING_MINUTE_START)
    end_time_marker = datetime(1, 1, 1, WORKING_HOUR_END, WORKING_MINUTE_END)
    now = datetime.now()
    today = datetime.now().date()
    current_dt = start_time_marker
    
    while current_dt <= end_time_marker:
        slot_str = current_dt.strftime("%I:%M %p")
        
        if current_date == today:
            full_slot_dt = datetime.combine(current_date, current_dt.time())
            # Only show slots that start at least 15 minutes from now
            if full_slot_dt >= (now + timedelta(minutes=14)):
                slots.append(slot_str)
        else:
            slots.append(slot_str)
            
        current_dt += timedelta(minutes=15)
        
    return slots

def prepare_events(bookings_list):
    """Converts internal booking data to the format required by streamlit-calendar (ISO strings)."""
    events = []
    for i, booking in enumerate(bookings_list):
        events.append({
            "id": str(i), 
            "title": f"[{booking['dept']}] {booking['purpose']} ({booking.get('attendees', 'N/A')} ppl)",
            # Store datetimes as ISO strings for the calendar component
            "start": booking["start"].isoformat(), 
            "end": booking["end"].isoformat(), 
            "color": PRIMARY_PURPLE,
            "resourceId": "RoomA"
        })
    return events

def update_calendar_key():
    """Generates a new, unique key for the calendar to force a full re-render after an update."""
    st.session_state.calendar_key = f"full_weekly_calendar_{uuid.uuid4()}"


# --- PAGE DEFINITIONS ---

def registration_page():
    
    st.markdown(f'<div class="login-card-container">', unsafe_allow_html=True)
    
    # Header Bar
    st.markdown(f"""
        <div class="login-header-bar">
            <h2>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15H9v-2h2v2zm0-4H9V7h2v6zm4 4h-2v-6h2v6z"/></svg>
                ZODOPT Registration
            </h2>
            <p>Create your account to start scheduling</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Form Body
    st.markdown('<div class="login-form-body">', unsafe_allow_html=True)
    
    with st.form("registration_form"):
        st.markdown('<p>Email Address</p>', unsafe_allow_html=True)
        new_email = st.text_input("", placeholder="you@zodopt.com", key="reg_email", label_visibility="collapsed").strip().lower()
        
        st.markdown('<p>Department</p>', unsafe_allow_html=True)
        department = st.selectbox("", options=DEPARTMENT_OPTIONS, key="reg_department", label_visibility="collapsed")
        
        st.markdown('<p>New Password</p>', unsafe_allow_html=True)
        new_password = st.text_input("", type="password", placeholder="Enter your password", key="reg_password", label_visibility="collapsed")
        
        st.markdown('<p>Confirm Password</p>', unsafe_allow_html=True)
        confirm_password = st.text_input("", type="password", placeholder="Confirm your password", key="reg_confirm_password", label_visibility="collapsed")
        
        st.write(" ") 
        register_button = st.form_submit_button("Register", type="primary", use_container_width=True)

    if register_button:
        if not new_email or "@" not in new_email:
            st.error("Please enter a valid Email ID.")
        elif department == "Select":
            st.error("Please select your department.")
        elif not new_password or len(new_password) < 6:
            st.error("Password must be at least 6 characters long.")
        elif new_password != confirm_password:
            st.error("Password and Confirm Password must match.")
        elif new_email in st.session_state.users:
            st.error(f"Email ID '{new_email}' is already taken.")
        else:
            st.session_state.users[new_email] = {
                "password": new_password, 
                "dept": department
            }
            st.success(f"Registration successful for **{new_email}**! Redirecting to login...")
            st.session_state.page = "login"
            st.rerun() 
            
    # Close Form Body Div
    st.markdown("</div>", unsafe_allow_html=True) 

    # --- REFINED FOOTER SECTION ---
    st.markdown('<div class="login-footer">', unsafe_allow_html=True) 
    
    col_dash, col_login = st.columns([1.5, 1])

    with col_dash:
        # Back to Dashboard button 
        if st.button("⬅️ Back to Dashboard", key="reg_back_to_dash"):
            # Set external navigation state to return to main app/dashboard
            if 'current_page' in st.session_state:
                st.session_state['current_page'] = 'main'
            st.session_state.logged_in_user = None
            st.rerun()

    with col_login:
        # Sign In button 
        if st.button("Sign In", key="nav_to_login", help="Already have an account? Sign in."):
            st.session_state.page = 'login'
            st.rerun()
    
    # Close Footer and Card Container Divs
    st.markdown("</div>", unsafe_allow_html=True) 
    st.markdown("</div>", unsafe_allow_html=True)


def login_page():
    """Renders the login interface styled to resemble the Visitplan image."""
    
    st.markdown(f'<div class="login-card-container">', unsafe_allow_html=True)

    # Header Bar
    st.markdown(f"""
        <div class="login-header-bar">
            <h2>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M19 3h-2v2h2v14h-2v2h2c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-9.9 14.1l-5.6-5.6c-.2-.2-.2-.5 0-.7l5.6-5.6c.3-.3.8-.1.8.3v3h7c.3 0 .5.2.5.5s-.2.5-.5.5h-7v3c0 .4-.5.6-.8.3z"/></svg>
                ZODOPT MeetEase Login
            </h2>
            <p>Sign in to manage your bookings and visits</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Form Body
    st.markdown('<div class="login-form-body">', unsafe_allow_html=True)
    
    with st.form("login_form"):
        st.markdown('<p>Email Address</p>', unsafe_allow_html=True)
        email = st.text_input("", placeholder="you@company.com", key="login_email", label_visibility="collapsed").strip().lower()

        st.markdown('<p>Password</p>', unsafe_allow_html=True)
        password = st.text_input("", type="password", placeholder="Enter your password", key="login_password", label_visibility="collapsed")
        
        col_check, col_forgot_placeholder = st.columns([1, 1])
        with col_check:
            st.checkbox("Remember me", key="remember_me")
        
        # Placeholder for alignment in the form (where the button used to be)
        with col_forgot_placeholder:
            st.markdown('<div style="height: 38px;"></div>', unsafe_allow_html=True) 

        st.write(" ") 
        submit_button = st.form_submit_button("Sign In →", type="primary", use_container_width=True)

    # --- FORGOT PASSWORD BUTTON IS MOVED HERE (OUTSIDE THE FORM) ---
    col_forgot_row = st.columns(1)[0]
    with col_forgot_row:
        # Use a div to apply the custom CSS targeting for the link-like button
        st.markdown('<div class="forgot-password-container">', unsafe_allow_html=True)
        # Add a column to push the button right
        col_dummy, col_btn = st.columns([1, 1])
        with col_btn:
            if st.button("Forgot password?", key="forgot_password_btn_outside", help="Click here to reset your password."):
                st.info("Forgot Password functionality is not yet implemented.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Login Success/Error Logic ---
    if submit_button:
        if email in st.session_state.users and st.session_state.users[email]["password"] == password:
            st.session_state.logged_in_user = email
            st.session_state.page = "calendar"
            st.success(f"Welcome, {email}! Redirecting...")
            st.rerun()
        else:
            st.error("Invalid Email Address or password.")

    # Close Form Body Div
    st.markdown("</div>", unsafe_allow_html=True) 

    # --- REFINED FOOTER SECTION ---
    st.markdown('<div class="login-footer">', unsafe_allow_html=True)
    
    col_dash, col_register = st.columns([1.5, 1])

    with col_dash:
        # Back to Dashboard button
        if st.button("⬅️ Back to Dashboard", key="login_back_to_dash"):
            # Set external navigation state to return to main app/dashboard
            if 'current_page' in st.session_state:
                st.session_state['current_page'] = 'main'
            st.session_state.logged_in_user = None
            st.rerun()

    with col_register:
        # Register button
        if st.button("Register", key="nav_to_register", help="Don't have an account? Register here."):
            st.session_state.page = 'register'
            st.rerun()

    # Close Footer and Card Container Divs
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def calendar_page():
    """Renders the main booking calendar application."""
    
    current_user = st.session_state.logged_in_user
    
    # --- HEADER & LOGOUT (Tighter Spacing) ---
    col_title, col_user, col_logout, col_logo = st.columns([5, 1.5, 1, 1])
    
    with col_title:
        st.markdown('<h2 style="color: #1f1f1f; margin-bottom: 0;">🗓️ ZODOPT MeetEase - Daily Conference Room Scheduler</h2>', unsafe_allow_html=True)
    
    with col_user:
        st.markdown(f'<div style="background-color: #ffffff; padding: 5px; border-radius: 8px; color: #1f1f1f; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 0.85rem; margin-top: 10px;">Logged in as: **{current_user}**</div>', unsafe_allow_html=True)
        
    with col_logout:
        if st.button("Logout", key="calendar_logout", help="Log out of the system"):
            st.session_state.logged_in_user = None
            st.session_state.page = "login"
            st.rerun()

    with col_logo:
        # Using a reliable placeholder for the logo since local file paths are unavailable
        st.markdown(f'<div style="width: 80px; height: 80px; background-color: {PRIMARY_PURPLE}; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-top: -15px;"><span style="color: white; font-weight: bold; font-size: 1.5rem;">Z</span></div>', unsafe_allow_html=True)

    st.markdown('<hr style="margin-top: 5px; margin-bottom: 20px;">', unsafe_allow_html=True)
    
    # --- CALENDAR & BOOKING FORM SECTION ---
    col_calendar, col_form = st.columns([3, 1]) 

    with col_calendar:
        # ---------------- CALENDAR DISPLAY ----------------
        st.markdown('<h3 style="margin-bottom: 10px;">Schedule View</h3>', unsafe_allow_html=True)

        slot_min_time_str = f"{WORKING_HOUR_START:02}:{WORKING_MINUTE_START:02}:00" 
        slot_max_time_str = f"{WORKING_HOUR_END:02}:{WORKING_MINUTE_END:02}:00" 

        calendar_options = {
            "slotMinTime": slot_min_time_str,
            "slotMaxTime": slot_max_time_str,
            "initialView": "timeGridDay", 
            "headerToolbar": {
                "left": "today prev,next",
                "center": "title",
                "right": "timeGridDay,timeGridWeek" 
            },
            "weekends": True,
            "height": 700,
            "slotDuration": "00:15:00", 
            "allDaySlot": False,
            # Customizing calendar appearance
            "eventColor": PRIMARY_PURPLE,
            "scrollTime": slot_min_time_str # Start calendar view at working hours
        }

        events_data = prepare_events(st.session_state.bookings)

        calendar_component = calendar(
            events=events_data,
            options=calendar_options,
            key=st.session_state.calendar_key 
        )

    with col_form:
        # ---------------- BOOKING FORM (CREATE NEW) ----------------
        st.markdown('<h3 style="margin-bottom: 10px;">👤👤👤 Book a Slot</h3>', unsafe_allow_html=True)

        min_time_display = START_TIME_DEFAULT.strftime('%I:%M %p')
        max_time_display = END_TIME_DEFAULT.strftime('%I:%M %p')

        # ATTENDEE POLICY ALERT
        st.markdown(f'<p style="color: #cc0000; font-weight: bold; font-size: 14px; margin-top: 0;">Booking requires {MIN_ATTENDEES} to {MAX_ATTENDEES} attendees.</p>', unsafe_allow_html=True)

        with st.form("weekly_booking_form"):
            st.markdown('<p>Date</p>', unsafe_allow_html=True)
            booking_date = st.date_input("", datetime.today().date(), min_value=datetime.today().date(), key="booking_date_input", label_visibility="collapsed")
            
            available_time_slots = generate_time_slots(booking_date)
            
            st.markdown('<p>Start Time (HH:MM AM/PM)</p>', unsafe_allow_html=True)
            start_time_str = st.selectbox("", options=available_time_slots, index=0, key="start_time_select", label_visibility="collapsed")
            
            st.markdown('<p>End Time (HH:MM AM/PM)</p>', unsafe_allow_html=True)
            end_time_str = st.selectbox("", options=available_time_slots, index=0, key="end_time_select", label_visibility="collapsed")
            
            st.markdown('<p>Number of People</p>', unsafe_allow_html=True)
            num_attendees = st.selectbox("", options=ATTENDEE_OPTIONS, index=0, key="attendees_select", label_visibility="collapsed")
            
            user_dept = st.session_state.users.get(current_user, {}).get('dept', 'Select')
            default_dept_index = DEPARTMENT_OPTIONS.index(user_dept) if user_dept in DEPARTMENT_OPTIONS else 0
            
            st.markdown('<p>Department</p>', unsafe_allow_html=True)
            # Department is pre-filled and disabled based on logged-in user
            department = st.selectbox("", options=DEPARTMENT_OPTIONS, index=default_dept_index, disabled=True, key="dept_select", label_visibility="collapsed")
            
            st.markdown('<p>Purpose</p>', unsafe_allow_html=True)
            purpose = st.selectbox("", options=PURPOSE_OPTIONS, index=0, key="purpose_select", label_visibility="collapsed")

            submit = st.form_submit_button("Book Slot", type="primary", use_container_width=True)

            if submit:
                # --- Validation logic ---
                if start_time_str == "Select" or end_time_str == "Select" or purpose == "Select":
                    st.warning("⚠️ Please select valid times and purpose.")
                    st.stop()

                if num_attendees == "Select":
                    st.warning(f"⚠️ Please select the number of attendees ({MIN_ATTENDEES} to {MAX_ATTENDEES}).")
                    st.stop()
                
                try:
                    attendees_count = int(num_attendees)
                except ValueError:
                    st.error("Invalid attendee count selected.")
                    st.stop()

                if not (MIN_ATTENDEES <= attendees_count <= MAX_ATTENDEES):
                    st.error(f"❌ Booking failed: You must have between {MIN_ATTENDEES} and {MAX_ATTENDEES} attendees.")
                    st.stop()
                    
                new_start_dt = time_slot_to_datetime(start_time_str, booking_date)
                new_end_dt = time_slot_to_datetime(end_time_str, booking_date)

                if new_end_dt is None or new_start_dt is None:
                    st.error("Error converting time string. Please re-select times.")
                    st.stop()
                    
                if new_end_dt <= new_start_dt:
                    st.warning("⚠️ End time must be after start time.")
                    st.stop()
                    
                min_dt = datetime.combine(booking_date, START_TIME_DEFAULT)
                max_dt = datetime.combine(booking_date, END_TIME_DEFAULT)

                if new_start_dt < min_dt or new_end_dt > max_dt:
                    st.warning(f"⚠️ Booking must be strictly within working hours: **{min_time_display}** to **{max_time_display}**.")
                    st.stop()
                
                now_buffer = datetime.now()
                if new_start_dt < now_buffer:
                    st.error("❌ The selected start time is already in the past. Please select an active slot.")
                    st.stop()
                    
                # Check for overlap
                overlap = any(b["start"] < new_end_dt and b["end"] > new_start_dt for b in st.session_state.bookings)
                
                if overlap:
                    st.error("❌ This time overlaps with an existing booking.")
                    st.stop()
                else:
                    # --- Successful Booking ---
                    new_booking = {
                        "start": new_start_dt, 
                        "end": new_end_dt, 
                        "dept": department,
                        "purpose": purpose,
                        "user": current_user,
                        "attendees": attendees_count
                    }
                    st.session_state.bookings.append(new_booking)
                    st.session_state.bookings.sort(key=lambda b: b['start'])
                    
                    logging.info(f"New Booking Added: User={current_user}, Start={new_start_dt.isoformat()}")

                    update_calendar_key()
                    st.success("✅ Booking confirmed! The schedule view has been updated.")
                    st.rerun()

        st.markdown('<hr style="margin-top: 15px; margin-bottom: 15px;">', unsafe_allow_html=True)
        
        # --- BOOKING MANAGEMENT SECTION ---
        st.markdown('<h3 style="margin-bottom: 10px;"> Manage Your Bookings</h3>', unsafe_allow_html=True)
        st.markdown('<p style="font-weight: 500; margin-top: 0;">Extend, check out early, or cancel a future booking.</p>', unsafe_allow_html=True)

        now = datetime.now() 
        
        user_bookings = [
            (i, b) for i, b in enumerate(st.session_state.bookings)
            if b["user"] == current_user and b["end"] > now
        ]
        
        if not user_bookings:
            st.info("You have no current or future bookings to manage.")
        else:
            booking_options = [
                f"({k+1}) {b['start'].strftime('%b %d, %I:%M %p')} - {b['end'].strftime('%I:%M %p')} for {b['purpose']} ({b.get('attendees', 'N/A')} ppl)"
                for k, (i, b) in enumerate(user_bookings)
            ]
            
            original_indices = [i for i, b in user_bookings]

            with st.form("booking_management_form"):
                
                st.markdown('<p>Select Booking to Manage</p>', unsafe_allow_html=True)
                selected_option = st.selectbox("", options=booking_options, index=0, key="manage_select", label_visibility="collapsed")
                
                selected_index_in_options = booking_options.index(selected_option)
                booking_index = original_indices[selected_index_in_options]
                current_booking = st.session_state.bookings[booking_index]
                booking_date_managed = current_booking["start"].date()
                
                management_slots = generate_time_slots(booking_date_managed)
                current_end_time_str = current_booking["end"].strftime("%I:%M %p")
                
                # Ensure current end time is in the list (might be filtered out if it's in the past)
                if current_end_time_str not in management_slots:
                    management_slots.append(current_end_time_str)
                    # Re-sort to maintain order
                    management_slots.sort(key=lambda x: datetime.strptime(x, "%I:%M %p") if x != "Select" else datetime.min)
                
                default_time_index = management_slots.index(current_end_time_str)
                
                st.markdown('<p>New End Time (for early checkout or extension)</p>', unsafe_allow_html=True)
                new_end_time_str = st.selectbox(
                    "",
                    options=management_slots,
                    index=default_time_index, 
                    key="new_end_time_select_manage",
                    label_visibility="collapsed"
                )

                col_update, col_cancel = st.columns([1, 1])
                with col_update:
                    update_button = st.form_submit_button("Update End Time", use_container_width=True)
                with col_cancel:
                    cancel_button = st.form_submit_button("Cancel Booking", use_container_width=True) 
                    
                if update_button:
                    # --- Update logic ---
                    if new_end_time_str == "Select":
                        st.error("❌ Please select a valid new end time.")
                        st.stop()
                        
                    new_end_dt_combined = time_slot_to_datetime(new_end_time_str, booking_date_managed)
                    
                    if new_end_dt_combined is None:
                        st.error("Error parsing new end time.")
                        st.stop()

                    if new_end_dt_combined <= current_booking["start"]:
                        st.error("❌ The new end time must be strictly **after** the start time of the booking.")
                        st.stop()
                        
                    max_end_dt = datetime.combine(booking_date_managed, END_TIME_DEFAULT)
                    
                    if new_end_dt_combined > max_end_dt:
                        st.error(f"❌ Cannot extend past the working hour end: **{max_end_dt.strftime('%I:%M %p')}**.")
                        st.stop()

                    if new_end_dt_combined < now:
                        st.error("❌ The new end time cannot be in the past.")
                        st.stop()

                    overlap_exists = False
                    # Check for overlap with other bookings (excluding the current one)
                    for i, b in enumerate(st.session_state.bookings):
                        if i != booking_index: 
                            # Check if the existing booking overlaps with the proposed new slot (current_start -> new_end)
                            if current_booking["start"] < b["end"] and b["start"] < new_end_dt_combined:
                                overlap_exists = True
                                break
                        
                    if overlap_exists:
                        st.error("❌ The updated time slot overlaps with another existing booking. Cannot modify.")
                        st.stop()
                        
                    st.session_state.bookings[booking_index]["end"] = new_end_dt_combined
                    
                    update_calendar_key()
                    st.success(f"✅ Booking updated! New End Time: **{new_end_dt_combined.strftime('%I:%M %p')}**.")
                    st.rerun()

                if cancel_button:
                    st.session_state.bookings.pop(booking_index)
                    
                    update_calendar_key()
                    st.success("🗑️ Booking has been successfully cancelled.")
                    st.rerun()


# --- CONFERENCE PAGE DISPATCHER (MAIN ENTRY POINT) ---

def conference_page():
    """Main function for the conference room scheduler module, handling internal navigation (login/register/calendar)."""
    
    # 1. Apply custom Visitplan styling
    apply_visitplan_style()
    
    # 2. Ensure state is initialized
    initialize_conference_state()
    
    # 3. Dispatch the correct page based on internal state
    if st.session_state.page == "calendar" and st.session_state.logged_in_user:
        calendar_page()
    elif st.session_state.page == "login":
        login_page()
    else: # Default page is now "login" or explicit "register"
        registration_page()

# This structure allows main.py to easily import and call `conference_page()`
# to render the entire subsystem.
