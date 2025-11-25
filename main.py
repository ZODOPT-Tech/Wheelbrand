# main.py - ZODOPT MeetEase Integrated Controller and Dashboard

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from PIL import Image
import os 
import base64 
import mimetypes 

# --- CONFIGURATION & PAGE SETUP ---

# NOTE: Ensure the path below is correct for your local environment
# Assuming the logo path is defined correctly based on the user's environment
LOGO_PATH = "C:\\Users\\DELL\\Documents\\zodopt\\images\\zodopt.png" 

# Define a standard background color for a clean look (light gray or white)
BACKGROUND_COLOR = "#f0f2f6" # Light gray for the main app background
CONTENT_CARD_COLOR = "#ffffff" # Pure white for containers/cards

# Define brand colors for navigation cards (matching the new card style)
PURPLE_PRIMARY = "#7B68EE"   # Purple for Vistplan
GREEN_PRIMARY = "#3CB371"    # Green for Conference Booking

# Time formats
LOGIC_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DISPLAY_TIME_FORMAT = '%I:%M %p'
DISPLAY_DATETIME_FORMAT = '%b %d, %I:%M %p'


st.set_page_config(
    page_title="ZODOPT",
    page_icon="🏠", # Using emoji fallback for the icon path
    layout="wide",
)

# --- CRITICAL: Ensure these imports succeed ---
try:
    # Ensure these are available if they exist
    from visitor import visitor_page
    from conference_page import conference_page
except ImportError as e:
    st.error(f"FATAL ERROR: Could not import module files. Please ensure visitor.py, and conference_page.py are in the same folder as main.py.")
    st.error(f"Import Error Details: {e}")


# ----------------------------------------------------------------------
# --- SESSION STATE INITIALIZATION (CLEARED DUMMY DATA) ---
# ----------------------------------------------------------------------

def initialize_app():
    """Initializes essential session state variables for all modules."""
    
    # 1. Main Navigation State
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'main' 
    
    # 2. Visitor Module State Initialization
    if 'visitor_logged_in' not in st.session_state:
        st.session_state['visitor_logged_in'] = False
        
    REQUIRED_VISITOR_KEYS = ['Time In', 'Name', 'Host', 'Company', 'Status', 'Time Out']
    if 'visitor_log_data' not in st.session_state:
        # Initialize with dummy data (for demonstration on first run)
        st.session_state['visitor_log_data'] = {
            'Time In': [datetime.now().strftime(LOGIC_TIME_FORMAT)],
            'Name': ['Test Visitor'],
            'Host': ['John Doe'],
            'Company': ['Acme Corp'],
            'Status': ['In Office'],
            'Time Out': ['']
        }
    else:
        for key in REQUIRED_VISITOR_KEYS:
            if key not in st.session_state['visitor_log_data']:
                st.session_state['visitor_log_data'][key] = []
    
    # Additional Visitor Keys
    if 'visitor_form_step' not in st.session_state: st.session_state['visitor_form_step'] = 1
    if 'temp_visitor_data' not in st.session_state: st.session_state['temp_visitor_data'] = {}
    if 'registration_complete' not in st.session_state: st.session_state['registration_complete'] = False
    if 'last_registered_name' not in st.session_state: st.session_state['last_registered_name'] = 'Visitor'

    # 3. Conference Module State Initialization
    if "bookings" not in st.session_state:
        # Initialize with empty list 
        st.session_state.bookings = []
        
    if "users" not in st.session_state:
        # Dummy user for demonstration (essential for login in conference_page)
        st.session_state.users = {"testuser@zodopt.com": {"password": "password123", "dept": "IT"}}
        
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "logged_in_user" not in st.session_state:
        st.session_state.logged_in_user = None

    
# --- UI STYLING & HELPERS ---

def set_background(image_path=None):
    """
    Sets the app background to a solid color and applies custom CSS styling,
    with a focus on ensuring the hidden buttons are programmatically clickable 
    without interfering with visible buttons.
    """
    st.markdown(f"""
        <style>
        /* Set the overall application background to a solid light color */
        .stApp {{
            background-color: {BACKGROUND_COLOR} !important;
            min-height: 100vh !important;
            padding: 0 !important;
            margin: 0 !important;
        }}
        
        /* Reset padding and margins for the main Streamlit container */
        [data-testid="stAppViewContainer"] {{ 
            padding: 0 !important; 
            margin: 0 !important; 
            background-color: transparent !important; 
        }}
        
        /* Remove header background */
        [data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}
        
        /* Style the main content block for centering and consistent padding */
        .main .block-container {{
            background-color: transparent !important;
            padding-top: 3rem;
            padding-bottom: 3rem;
            max-width: 100% !important;
            padding-left: 5rem;
            padding-right: 5rem;
        }}
        
        /* Style for Logs container to look like cards */
        .log-card-container {{
            background-color: {CONTENT_CARD_COLOR} !important; 
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); 
            border: 1px solid #e0e0e0; 
        }}

        /* Text color reset */
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText, div[data-testid="stCaption"] {{
            color: #1f1f1f !important; 
            text-shadow: none; 
        }}
        
        /* Custom Title style */
        .main-title {{
            color: #1a1a2e;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            text-shadow: none;
        }}
        
        /* --- NAVIGATION CARD STYLING (The full box acts as a button) --- */
        .nav-card-button {{
            background-color: {CONTENT_CARD_COLOR}; 
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border: 1px solid #e0e0e0;
        }}
        
        .nav-card-button:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        }}
        
        /* Icon container with background gradient/color */
        .icon-circle-box {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 15px;
            color: white; 
        }}
        
        .icon-vistplan {{
            background: linear-gradient(135deg, {PURPLE_PRIMARY}, #9370DB); 
            box-shadow: 0 5px 10px rgba(123, 104, 238, 0.4);
        }}
        
        .icon-conference {{
            background: linear-gradient(135deg, {GREEN_PRIMARY}, #66CDAA); 
            box-shadow: 0 5px 10px rgba(60, 179, 113, 0.4);
        }}

        .card-icon {{
            font-size: 2.5rem;
            line-height: 1; 
        }}
        
        .card-title {{
            font-size: 1.25rem;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
        }}

        .card-underline {{
            width: 40px;
            height: 3px;
            border-radius: 2px;
            margin-top: 5px;
        }}

        .underline-vistplan {{ background-color: {PURPLE_PRIMARY}; }}
        .underline-conference {{ background-color: {GREEN_PRIMARY}; }}

        /* --- CRITICAL NAVIGATION FIX (Refined for Isolation) --- 
           Target only the specific hidden navigation buttons by their data-testid 
           to ensure 'Sign Out' and other visible buttons are not affected.
        */
        div[data-testid="stButton-nav_btn_visitor"], 
        div[data-testid="stButton-nav_btn_conference"] {{
            position: absolute;
            left: -5000px;
            top: -5000px;
            z-index: -1; /* Ensure it doesn't block the visible cards */
            width: 1px;
            height: 1px;
            overflow: hidden;
        }}

        /* Ensure the columns fill their space for the click handler to work */
        [data-testid="stColumn"] {{
            height: 100%;
        }}

        /* Metric container card style */
        [data-testid="stMetric"] {{
            background-color: {CONTENT_CARD_COLOR};
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            border: 1px solid #e0e0e0;
        }}
        
        </style>
    """, unsafe_allow_html=True)


def render_header_and_navigation():
    """Renders the ZODOPT title, logo, and the clickable navigation cards."""
    
    # 1. Title and Logo (Kept outside any generic card container)
    col_title, col_logo = st.columns([9, 1])
    
    with col_title:
        st.markdown('<h1 class="main-title">ZODOPT</h1>', unsafe_allow_html=True)
    
    with col_logo:
        try:
            # Assuming LOGO_PATH is correct or the user will replace it
            logo_img = Image.open(LOGO_PATH)
            st.image(logo_img, width=80) 
        except Exception:
            # Placeholder text if logo is not found
            st.markdown(f'<div style="width: 80px; height: 80px; background-color: #f0f0f0; border-radius: 8px; text-align: center; line-height: 80px;">LOGO</div>', unsafe_allow_html=True)
    
    # 2. Navigation Cards (Quick Actions)
    st.container()
    nav_cols = st.columns(2)
    
    # --- VISTPLAN CARD (Visual component in column 0) ---
    with nav_cols[0]:
        # Using a div with an explicit onclick to trigger the hidden Streamlit button
        st.markdown(
            f"""
            <div class="nav-card-button" onclick="document.getElementById('nav_btn_visitor').click()">
                <div class="icon-circle-box icon-vistplan">
                    <span class="card-icon">📋</span> 
                </div>
                <div class="card-title">Vistplan</div>
                <div class="card-underline underline-vistplan"></div>
            </div>
            """, unsafe_allow_html=True
        )

    # --- CONFERENCE BOOKING CARD (Visual component in column 1) ---
    with nav_cols[1]:
        # Using a div with an explicit onclick to trigger the hidden Streamlit button
        st.markdown(
            f"""
            <div class="nav-card-button" onclick="document.getElementById('nav_btn_conference').click()">
                <div class="icon-circle-box icon-conference">
                    <span class="card-icon">🗓️</span>
                </div>
                <div class="card-title">Conference Booking</div>
                <div class="card-underline underline-conference"></div>
            </div>
            """, unsafe_allow_html=True
        )
        
    # --- HIDDEN STREAMLIT BUTTONS (Must be rendered for the JavaScript click to work) ---
    
    # Vistplan Hidden Button
    if st.button('Vistplan (Hidden)', key="nav_btn_visitor", use_container_width=True):
        st.session_state['current_page'] = 'visitor'
        st.rerun()

    # Conference Room Hidden Button
    if st.button('Conference Room (Hidden)', key="nav_btn_conference", use_container_width=True):
        st.session_state['current_page'] = 'conference'
        st.session_state['page'] = 'login' 
        st.rerun()


# --- CORE DASHBOARD LOGIC (No Change) ---

def sign_out_visitor(index):
    """
    Updates the visitor log for the entry at the given index.
    Sets Time Out to the current time and Status to 'Signed Out'.
    """
    if 'visitor_log_data' in st.session_state:
        log_data = st.session_state['visitor_log_data']
        
        if 0 <= index < len(log_data.get('Status', [])):
            log_data['Time Out'][index] = datetime.now().strftime(LOGIC_TIME_FORMAT)
            log_data['Status'][index] = 'Signed Out'
            
            st.toast(f"Visitor '{log_data['Name'][index]}' signed out successfully!")
            st.rerun()


def main_dashboard_content():
    """Renders the main dashboard content with metrics and side-by-side logs."""
    
    visitor_log = st.session_state['visitor_log_data']
    bookings_list = st.session_state['bookings'] 
    
    # --- Data Processing ---
    
    # 1. Visitor Data
    log_df = pd.DataFrame(visitor_log) if visitor_log and visitor_log.get('Name') else pd.DataFrame()
    current_visitors_df = log_df[log_df['Status'] == 'In Office'] if not log_df.empty else pd.DataFrame()
    
    # 2. Booking Data
    booking_df = pd.DataFrame(bookings_list) if bookings_list else pd.DataFrame()
    
    if not booking_df.empty:
        if 'dept' in booking_df.columns:
            booking_df = booking_df.rename(columns={'dept': 'Department'})
        
        now = datetime.now()
        
        # Filter out past bookings and sort
        if 'end' in booking_df.columns and 'start' in booking_df.columns:
            # Ensure columns are datetime objects
            booking_df['start'] = pd.to_datetime(booking_df['start'], errors='coerce')
            booking_df['end'] = pd.to_datetime(booking_df['end'], errors='coerce')
            
            booking_df = booking_df[
                booking_df['end'].dt.tz_localize(None) > now 
            ].sort_values(by='start').reset_index(drop=True)
        else:
            booking_df = pd.DataFrame() 

    # --- Metrics Section (Dashboard Overview) ---
    st.markdown("---") # Add a divider below the navigation cards
    col1, col2, col3 = st.columns(3) 
    
    with col1:
        st.metric(label="👥 Currently Signed In", value=len(current_visitors_df), delta_color='off')

    with col2:
        st.metric(label="🗓️ Total Upcoming Bookings", value=len(booking_df), delta_color='off')
        
    with col3:
        total_check_ins_today = 0
        if not log_df.empty and 'Time In' in log_df.columns:
             log_df['Time In DT'] = pd.to_datetime(log_df['Time In'], errors='coerce')
             total_check_ins_today = log_df[
                 log_df['Time In DT'].dt.date == datetime.now().date()
             ].shape[0]

        st.metric(label="🚶 Total Check-ins Today", value=total_check_ins_today, delta_color='off')

    st.markdown("---") 

    # --- Logs Section (Side-by-Side) ---
    col_visitor_log, col_booking_log = st.columns([3, 2])
    
    # --- VISITOR ACTIVITY LOG ---
    with col_visitor_log:
        st.markdown('<div class="log-card-container"><h3>📄 Visitor Activity Log</h3>', unsafe_allow_html=True)

        if not log_df.empty and log_df.shape[0] > 0:
            try:
                # Time conversion for display
                log_df['Display Time In'] = pd.to_datetime(log_df['Time In']).dt.strftime(DISPLAY_TIME_FORMAT)
                log_df['Display Time Out'] = pd.to_datetime(log_df['Time Out'], errors='coerce').dt.strftime(DISPLAY_TIME_FORMAT).fillna('-')
                
                log_df['original_index'] = log_df.index
                
                # Sorting: 'In Office' first, then latest 'Time In' first
                log_df['sort_key'] = log_df['Status'].apply(lambda x: 0 if x == 'In Office' else 1)
                display_df = log_df.sort_values(by=['sort_key', 'Time In'], ascending=[True, False]).reset_index(drop=True).copy()
                
                # Column Specs and Header
                col_spec = [1.5, 2.5, 2, 2, 1.5, 1.5, 1.5] 
                cols_header = st.columns(col_spec)
                
                for c, name in zip(cols_header, ["Time In", "Name", "Host", "Company", "Status", "Time Out", "Action"]):
                    c.markdown(f"**{name}**")
                    
                st.markdown('<hr style="margin: 0.5rem 0 0.5rem 0; border-top: 1px solid #ddd;">', unsafe_allow_html=True)
                
                # Data Rows
                for i in range(len(display_df)):
                    row = display_df.iloc[i]
                    original_index = row['original_index'] 
                    
                    cols = st.columns(col_spec)
                    cols[0].write(row['Display Time In'])
                    cols[1].write(row['Name'])
                    cols[2].write(row['Host'])
                    cols[3].write(row['Company'])
                    
                    if row['Status'] == 'In Office':
                        cols[4].markdown(f"**<span style='color:green;'>{row['Status']}</span>**", unsafe_allow_html=True) 
                    else:
                        cols[4].write(row['Status'])
                        
                    cols[5].write(row['Display Time Out'])
                    
                    with cols[6]:
                        if row['Status'] == 'In Office':
                            if st.button("🚪 Sign Out", key=f"sign_out_{original_index}", use_container_width=True, type='primary'):
                                sign_out_visitor(original_index)
                        else:
                            st.markdown("<div style='text-align:center;'>✅</div>", unsafe_allow_html=True)
                            
            except Exception as e:
                st.error(f"An unexpected error occurred while rendering the visitor log table: {e}")
                
        else:
            st.info("No visitor data currently available.")
            
        st.markdown('</div>', unsafe_allow_html=True)


    # --- CONFERENCE ROOM BOOKING LOG ---
    with col_booking_log:
        st.markdown('<div class="log-card-container"><h3>🗓️ Upcoming Room Bookings</h3>', unsafe_allow_html=True)
        
        if not booking_df.empty and booking_df.shape[0] > 0:
            booking_df['Display From'] = booking_df['start'].dt.strftime(DISPLAY_DATETIME_FORMAT)
            booking_df['Display To'] = booking_df['end'].dt.strftime(DISPLAY_TIME_FORMAT)
            
            booking_col_spec = [3, 2, 1.5] 
            cols_header = st.columns(booking_col_spec)
            
            for c, name in zip(cols_header, ["Department & Purpose", "Starts", "Ends"]):
                c.markdown(f"**{name}**")
            
            st.markdown('<hr style="margin: 0.5rem 0 0.5rem 0; border-top: 1px solid #ddd;">', unsafe_allow_html=True)
            
            # Data Rows
            for i in range(len(booking_df)):
                row = booking_df.iloc[i]
                
                cols = st.columns(booking_col_spec)
                
                cols[0].markdown(f"""
                    **{row['Department']}**<br>
                    <small>Purpose: {row.get('purpose', 'N/A')}</small><br>
                    <small>User: {row.get('user', 'N/A')} ({row.get('attendees', 'N/A')} ppl)</small>
                """, unsafe_allow_html=True)
                
                cols[1].write(row['Display From'])
                cols[2].write(row['Display To'])
                
        else:
            st.info("No upcoming room bookings found.")
            
        st.markdown('</div>', unsafe_allow_html=True)


# --- MAIN EXECUTION LOOP ---

def main():
    initialize_app()
    set_background() 
    
    current_page = st.session_state.get('current_page', 'main')

    if current_page == 'main':
        render_header_and_navigation() # Renders Title, Logo, and Navigation Cards
        main_dashboard_content() 
        
    elif current_page == 'visitor':
        # REMOVED: '← Back to Dashboard' button as requested.
        visitor_page()
        
    elif current_page == 'conference':
        # REMOVED: '← Back to Dashboard' button as requested.
        conference_page()
        
    else:
        st.error("Navigation error: Unknown page requested. Returning to Dashboard.")
        st.session_state['current_page'] = 'main'
        st.rerun()

if __name__ == '__main__':
    main()
