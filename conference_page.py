import streamlit as st
from datetime import datetime, time, timedelta
from streamlit_calendar import calendar
import uuid
import logging
import os

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONFIGURATION ---

# NOTE: ADJUST PATHS HERE if necessary
# LOGO_PATH = "C:\\Users\\DELL\\Documents\\zodopt\\images\\zodopt.png" # Using placeholder
LOGO_PATH = "placeholder_logo.png"

# UI Colors (Primary color is now the dark purple)
PRIMARY_PURPLE = "#5b46b2"  
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
        # Default test user for quick login
        st.session_state.users = {"testuser@zodopt.com": {"password": "password123", "dept": "IT"}}
    
    # *** SET DEFAULT PAGE TO 'register' ***
    if "page" not in st.session_state:
        st.session_state.page = "register"  
        
    if "logged_in_user" not in st.session_state:
        st.session_state.logged_in_user = None
    if "calendar_key" not in st.session_state:
        st.session_state.calendar_key = "full_weekly_calendar_0"

# --- UTILITY & UI FUNCTIONS ---

def apply_visitplan_style():
    """Applies CSS for purple buttons, card layout, and side-by-side footer links."""
    st.markdown(f"""
        <style>
        /* 1. Global Background and Layout */
        .stApp {{
            background-color: #f0f2f6 !important;  
            min-height: 100vh !important;  
        }}

        /* 2. Primary Button Color (PURPLE) */
        .stButton button, [data-testid="baseButton-primary"] {{
            background-color: {PRIMARY_PURPLE} !important;
            border-color: {PRIMARY_PURPLE} !important;
            color: white !important;
            border-radius: 4px;
            font-weight: 500;
        }}
        .stButton button:hover, [data-testid="baseButton-primary"]:hover {{
            background-color: #4b3992 !important;  
            border-color: #4b3992 !important;
        }}
        
        /* 3. Input Field Styling */
        .stTextInput > div > div > input,  
        .stSelectbox > div > button,
        .stDateInput > div > div > input {{
            background-color: #f7f7f7 !important;  
            border: 1px solid #ccc !important;
            border-radius: 4px;
            padding: 10px 12px;
            box-shadow: none !important;
        }}
        
        /* 4. Login Card Container Styling */
        .login-card-container {{
            max-width: {LOGIN_CARD_WIDTH};
            margin: 0 auto;  
            margin-top: 50px;  
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            overflow: hidden;  
            padding: 0;
        }}
        
        /* 5. Header Bar Styling */
        .login-header-bar {{
            background: {HEADER_GRADIENT};
            padding: 20px 30px;
            color: white;
            border-radius: 8px 8px 0 0;
        }}
        .login-header-bar h2 {{
            color: white !important;
            text-shadow: none;
            margin: 0;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
        }}
        .login-header-bar p {{
            color: #d1d5db !important;
            margin: 5px 0 0 0;
            font-size: 0.9rem;
        }}
        .login-header-bar svg {{
            margin-right: 15px;
            font-size: 2.2rem;
            fill: white;
        }}
        
        /* 6. Form Body Padding */
        .login-form-body {{
            padding: 30px;
        }}
        
        /* 7. Footer Styling (Side-by-side container) */
        .login-footer {{
            display: flex;  
            justify-content: space-between;  
            align-items: center;
            padding: 15px 30px;  
            border-top: 1px solid #eee;
            background-color: #fafafa;
            border-radius: 0 0 8px 8px;
            gap: 10px;  
        }}
        .login-footer p {{
            color: #4a4a4a;
            margin: 0;
            font-size: 0.9rem;
            white-space: nowrap;  
        }}
        .login-footer a {{
            color: {PRIMARY_PURPLE};  
            text-decoration: none;
            font-weight: 500;
        }}
        
        /* Style the 'Back to Dashboard' button using Streamlit button styling */
        /* Targets the secondary button specifically in the footer */
        .login-footer [data-testid="stButton"] button {{
            background-color: #ffffff !important;
            border: 1px solid #ccc !important;
            color: #4a4a4a !important;
            padding: 5px 10px;
            height: 38px;
            font-size: 0.9rem;
        }}
        .login-footer [data-testid="stButton"] button:hover {{
            background-color: #f0f0f0 !important;
        }}
        
        /* Ensure the right-aligned text is properly positioned */
        .right-aligned-text {{
            text-align: right;  
            margin-top: 5px;
        }}
        
        /* Specific styling to make the registration button look like a link */
        #login_nav_to_register button {{
            background-color: transparent !important;
            border: none !important;
            color: {PRIMARY_PURPLE} !important;
            font-weight: 500 !important;
            padding: 0 !important;
            height: auto !important;
        }}
        #login_nav_to_register button:hover {{
             background-color: transparent !important;
             text-decoration: underline;
        }}


        /* Ensure text is dark and readable everywhere else */
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText, div[data-testid="stCaption"] {{
            color: #1f1f1f !important;  
            text-shadow: none;  
        }}
        </style>
    """, unsafe_allow_html=True)


def time_slot_to_datetime(time_str, date_obj):
    # ... (function body remains the same)
    if time_str == "Select":
        return None
    try:
        time_obj = datetime.strptime(time_str, "%I:%M %p").time()
        return datetime.combine(date_obj, time_obj)
    except ValueError:
        return None

def generate_time_slots(current_date):
    # ... (function body remains the same)
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
            if full_slot_dt >= (now + timedelta(minutes=14)):
                slots.append(slot_str)
        else:
            slots.append(slot_str)
            
        current_dt += timedelta(minutes=15)
        
    return slots

def prepare_events(bookings_list):
    # ... (function body remains the same)
    events = []
    for i, booking in enumerate(bookings_list):
        events.append({
            "id": str(i),  
            "title": f"[{booking['dept']}] {booking['purpose']} ({booking.get('attendees', 'N/A')} ppl)",
            "start": booking["start"].isoformat(),  
            "end": booking["end"].isoformat(),    
            "color": PRIMARY_PURPLE,  
            "resourceId": "RoomA"  
        })
    return events

def update_calendar_key():
    # ... (function body remains the same)
    st.session_state.calendar_key = f"full_weekly_calendar_{uuid.uuid4()}"


# --- PAGE DEFINITIONS ---

def registration_page():
    
    st.markdown(f'<div class="login-card-container">', unsafe_allow_html=True)
    
    # Header Bar
    st.markdown(f"""
        <div class="login-header-bar">
            <h2>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15H9v-2h2v2zm0-4H9V7h2v6zm4 4h-2v-6h2v6z"/></svg>
                ZODOPT Registration
            </h2>
            <p>Create your account to start scheduling</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Form Body
    st.markdown('<div class="login-form-body">', unsafe_allow_html=True)
    
    with st.form("registration_form"):
        st.markdown('<p style="font-weight: 500; margin-bottom: 5px;">Email Address</p>', unsafe_allow_html=True)
        new_email = st.text_input("", placeholder="you@zodopt.com", key="reg_email").strip().lower()
        
        st.markdown('<p style="font-weight: 500; margin-bottom: 5px; margin-top: 15px;">Department</p>', unsafe_allow_html=True)
        department = st.selectbox("", options=DEPARTMENT_OPTIONS, key="reg_department")
        
        st.markdown('<p style="font-weight: 500; margin-bottom: 5px; margin-top: 15px;">New Password</p>', unsafe_allow_html=True)
        new_password = st.text_input("", type="password", placeholder="Enter your password", key="reg_password")
        
        st.markdown('<p style="font-weight: 500; margin-bottom: 5px; margin-top: 15px;">Confirm Password</p>', unsafe_allow_html=True)
        confirm_password = st.text_input("", type="password", placeholder="Confirm your password", key="reg_confirm_password")
        
        st.write(" ")  
        # Main registration button
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
            # Successful Registration
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
    
    col_dash, col_login = st.columns([1, 1])

    with col_dash:
        # Back to Dashboard button (Streamlit native)
        if st.button("⬅️ Back to Dashboard", key="reg_back_to_dash"):
            if 'current_page' in st.session_state:
                st.session_state['current_page'] = 'main'
            st.session_state.logged_in_user = None
            st.rerun()

    with col_login:
        # Sign In button/link
        st.markdown('<div class="right-aligned-text">', unsafe_allow_html=True)
        # Use HTML/Markdown to display the descriptive text
        st.markdown('<p>Already have an account? ', unsafe_allow_html=True) 
        # Use a standard Streamlit button outside the form for reliable navigation, styled to look like a link
        if st.button("Sign In", key="reg_nav_to_login"):
            st.session_state.page = "login"
            st.rerun()
        st.markdown('</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


    # Close Footer and Card Container Divs
    st.markdown("</div>", unsafe_allow_html=True)  
    st.markdown("</div>", unsafe_allow_html=True)
    

def login_page():
    """Renders the login interface styled to resemble the Visitplan image, plus registration button."""
    
    st.markdown(f'<div class="login-card-container">', unsafe_allow_html=True)

    # Header Bar
    st.markdown(f"""
        <div class="login-header-bar">
            <h2>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M19 3h-2v2h2v14h-2v2h2c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-9.9 14.1l-5.6-5.6c-.2-.2-.2-.5 0-.7l5.6-5.6c.3-.3.8-.1.8.3v3h7c.3 0 .5.2.5.5s-.2.5-.5.5h-7v3c0 .4-.5.6-.8.3z"/></svg>
                ZODOPT MeetEase Login
            </h2>
            <p>Sign in to manage your bookings and visits</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Form Body
    st.markdown('<div class="login-form-body">', unsafe_allow_html=True)
    
    with st.form("login_form"):
        # ---------------------------------------------
        # Fields to match the image structure
        # ---------------------------------------------
        st.markdown('<p style="font-weight: 500; margin-bottom: 5px;">Email Address</p>', unsafe_allow_html=True)
        # To better match the image, we can optionally add a mailbox icon (but Streamlit doesn't support custom icons in text input directly)
        email = st.text_input("", placeholder="you@company.com", key="login_email").strip().lower()

        st.markdown('<p style="font-weight: 500; margin-bottom: 5px; margin-top: 15px;">Password</p>', unsafe_allow_html=True)
        password = st.text_input("", type="password", placeholder="Enter your password", key="login_password")
        
        # Checkbox and Forgot Password Link on the same row
        col_check, col_forgot = st.columns([1, 1])
        with col_check:
            st.checkbox("Remember me", key="remember_me", label_visibility="visible") # Added label_visibility to ensure checkbox shows
        with col_forgot:
            # Using Markdown to replicate the look of a hyperlink
            st.markdown('<div style="text-align: right; margin-top: 8px;"><a href="#" style="color: #a855f7; text-decoration: none; font-weight: 500;">Forgot password?</a></div>', unsafe_allow_html=True)
        
        st.write(" ")  
        # Primary Sign In button
        submit_button = st.form_submit_button("Sign In →", type="primary", use_container_width=True)

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
    
    col_dash, col_register = st.columns([1, 1])

    with col_dash:
        # Back to Dashboard button (Streamlit native)
        if st.button("⬅️ Back to Dashboard", key="login_back_to_dash"):
            if 'current_page' in st.session_state:
                st.session_state['current_page'] = 'main'
            st.session_state.logged_in_user = None
            st.rerun()

    with col_register:
        # New Registration button/link
        st.markdown('<div class="right-aligned-text">', unsafe_allow_html=True)
        st.markdown('<p>Don\'t have an account? ', unsafe_allow_html=True) 
        
        # Use a standard Streamlit button, styled using CSS ID #login_nav_to_register 
        if st.button("Register", key="login_nav_to_register"):
            st.session_state.page = "register"
            st.rerun()
            
        st.markdown('</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


    # Close Footer and Card Container Divs
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def calendar_page():
    # ... (function body remains the same)
    
    current_user = st.session_state.logged_in_user
    
    # --- HEADER & LOGOUT ---
    col_title, col_user, col_logout, col_logo = st.columns([5, 1.5, 1, 1])
    
    with col_title:
        st.markdown('<h2 style="color: #1f1f1f;">🗓️ ZODOPT MeetEase - Daily Conference Room Scheduler</h2>', unsafe_allow_html=True)
    
    with col_user:
        st.markdown(f'<div style="background-color: #ffffff; padding: 5px; border-radius: 8px; color: #1f1f1f; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">Logged in as: **{current_user}**</div>', unsafe_allow_html=True)
        
    with col_logout:
        st.write(" ")  
        if st.button("Logout", key="calendar_logout"):
            st.session_state.logged_in_user = None
            st.session_state.page = "login"
            st.rerun()

    with col_logo:
        try:
            # Assuming LOGO_PATH is set up correctly in your environment
            st.image(LOGO_PATH, width=80)  
        except FileNotFoundError:
            st.info("Logo placeholder.")

    st.write("---")
    
    # --- CALENDAR & BOOKING FORM SECTION ---
    col_calendar, col_form = st.columns([2, 1])

    with col_calendar:
        # ---------------- CALENDAR DISPLAY ----------------
        st.markdown('<h3>Schedule View</h3>', unsafe_allow_html=True)

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
        }

        events_data = prepare_events(st.session_state.bookings)

        calendar_component = calendar(
            events=events_data,
            options=calendar_options,
            key=st.session_state.calendar_key  
        )

    with col_form:
        # ---------------- BOOKING FORM (CREATE NEW) ----------------
        st.markdown('<h3>👤👤👤 Book a Slot</h3>', unsafe_allow_html=True)

        min_time_display = START_TIME_DEFAULT.strftime('%I:%M %p')
        max_time_display = END_TIME_DEFAULT.strftime('%I:%M %p')

        # ATTENDEE POLICY ALERT
        st.markdown(f'<p style="color: #cc0000; font-weight: bold; font-size: 14px;">Booking requires {MIN_ATTENDEES} to {MAX_ATTENDEES} attendees.</p>', unsafe_allow_html=True)

        with st.form("weekly_booking_form"):
            st.markdown('<p style="font-weight: 500; margin-bottom: 5px;">Date</p>', unsafe_allow_html=True)
            booking_date = st.date_input("", datetime.today().date(), min_value=datetime.today().date(), key="booking_date_input")
            
            available_time_slots = generate_time_slots(booking_date)
            
            st.markdown('<p style="font-weight: 500; margin-bottom: 5px; margin-top: 15px;">Start Time (HH:MM AM/PM)</p>', unsafe_allow_html=True)
            start_time_str = st.selectbox("", options=available_time_slots, index=0, key="start_time_select")
            
            st.markdown('<p style="font-weight: 500; margin-bottom: 5px; margin-top: 15px;">End Time (HH:MM AM/PM)</p>', unsafe_allow_html=True)
            end_time_str = st.selectbox("", options=available_time_slots, index=0, key="end_time_select")
            
            st.markdown('<p style="font-weight: 500; margin-bottom: 5px; margin-top: 15px;">Number of People</p>', unsafe_allow_html=True)
            num_attendees = st.selectbox("", options=ATTENDEE_OPTIONS, index=0, key="attendees_select")
            
            user_dept = st.session_state.users.get(current_user, {}).get('dept', 'Select')
            default_dept_index = DEPARTMENT_OPTIONS.index(user_dept) if user_dept in DEPARTMENT_OPTIONS else 0
            
            st.markdown('<p style="font-weight: 500; margin-bottom: 5px; margin-top: 15px;">Department</p>', unsafe_allow_html=True)
            department = st.selectbox("", options=DEPARTMENT_OPTIONS, index=default_dept_index, disabled=True, key="dept_select")
            
            st.markdown('<p style="font-weight: 500; margin-bottom: 5px; margin-top: 15px;">Purpose</p>', unsafe_allow_html=True)
            purpose = st.selectbox("", options=PURPOSE_OPTIONS, index=0, key="purpose_select")

            submit = st.form_submit_button("Book Slot", type="primary", use_container_width=True)

            if submit:
                # --- Validation ---
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
                
                now = datetime.now()
                if new_start_dt < now:
                    st.error("❌ The selected start time is already in the past. Please select an active slot.")
                    st.stop()
                    
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

        st.write("---")
        
        # --- BOOKING MANAGEMENT SECTION ---
        st.markdown('<h3> Manage Your Bookings</h3>', unsafe_allow_html=True)
        st.markdown('<p style="font-weight: 500;">Extend, check out early, or cancel a future booking.</p>', unsafe_allow_html=True)

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
                
                st.markdown('<p style="font-weight: 500; margin-bottom: 5px;">Select Booking to Manage</p>', unsafe_allow_html=True)
                selected_option = st.selectbox("", options=booking_options, index=0, key="manage_select")
                
                selected_index_in_options = booking_options.index(selected_option)
                booking_index = original_indices[selected_index_in_options]
                current_booking = st.session_state.bookings[booking_index]
                booking_date_managed = current_booking["start"].date()
                
                management_slots = generate_time_slots(booking_date_managed)
                current_end_time_str = current_booking["end"].strftime("%I:%M %p")
                
                if current_end_time_str not in management_slots:
                    management_slots.append(current_end_time_str)
                    management_slots.sort(key=lambda x: datetime.strptime(x, "%I:%M %p") if x != "Select" else datetime.min)
                
                default_time_index = management_slots.index(current_end_time_str)
                
                st.markdown('<p style="font-weight: 500; margin-bottom: 5px; margin-top: 15px;">New End Time (for early checkout or extension)</p>', unsafe_allow_html=True)
                new_end_time_str = st.selectbox(
                    "",
                    options=management_slots,
                    index=default_time_index,  
                    key="new_end_time_select_manage"
                )

                col_update, col_cancel = st.columns([1, 1])
                with col_update:
                    update_button = st.form_submit_button("Update End Time", use_container_width=True)
                with col_cancel:
                    cancel_button = st.form_submit_button("Cancel Booking", use_container_width=True)  
                    
                if update_button:
                    
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
                    for i, b in enumerate(st.session_state.bookings):
                        if i != booking_index:  
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


# --- CONFERENCE PAGE DISPATCHER ---

def conference_page():
    """Main function for the conference room scheduler module."""
    
    # 1. Apply custom Visitplan styling
    apply_visitplan_style()
    
    # 2. Ensure state is initialized
    initialize_conference_state()
    
    # 3. Dispatch the correct page
    if st.session_state.page == "calendar" and st.session_state.logged_in_user:
        calendar_page()
    elif st.session_state.page == "login":
        login_page()
    else: # Default page is "register"
        registration_page()
        
# Execute the main function
# conference_page()