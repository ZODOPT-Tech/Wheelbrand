# main.py - ZODOPT MeetEase Integrated Controller and Dashboard

import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import json
import boto3
import mysql.connector
from botocore.exceptions import ClientError
# Removed os, base64, mimetypes as they are not used in the core logic

# --- CRITICAL: Ensure these imports succeed ---
try:
    # Ensure these are available if they exist
    from visitor import visitor_page
    from conference_page import conference_page
except ImportError as e:
    st.error(f"FATAL ERROR: Could not import module files. Please ensure visitor.py, and conference_page.py are in the same folder as main.py.")
    st.error(f"Import Error Details: {e}")
    st.stop()


# ======================================================================
# --- 1. CONFIGURATION & TIME/COLOR DEFINITIONS ---
# ======================================================================

# NOTE: Ensure the path below is correct for your local environment
LOGO_PATH = "C:\\Users\\DELL\\Documents\\zodopt\\images\\zodopt.png" 

# Define a standard background color
BACKGROUND_COLOR = "#f0f2f6" 
CONTENT_CARD_COLOR = "#ffffff" 

# Define brand colors 
PURPLE_PRIMARY = "#7B68EE"   
GREEN_PRIMARY = "#3CB371"    

# Time formats
LOGIC_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DISPLAY_TIME_FORMAT = '%I:%M %p'
DISPLAY_DATETIME_FORMAT = '%b %d, %I:%M %p'


st.set_page_config(
    page_title="ZODOPT",
    page_icon="🏠",
    layout="wide",
)


# ======================================================================
# --- 2. DATABASE CONNECTOR LOGIC (INTEGRATED AND FIXED) ---
# ======================================================================

# --- AWS SECRETS MANAGER CONFIG (FIXED SECRET NAME) ---
HARDCODED_SECRET_NAME = 'Wheelbrand' # <--- FIXED based on the image provided
HARDCODED_REGION = 'ap-south-1' 
SECRET_KEYS = {
    'host_key': 'DB_HOST',
    'database_key': 'DB_NAME',
    'user_key': 'DB_USER',
    'password_key': 'DB_PASSWORD'
}

@st.cache_resource
def get_secret():
    """Retrieves MySQL credentials from AWS Secrets Manager."""
    secret_name = HARDCODED_SECRET_NAME
    region_name = HARDCODED_REGION

    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # ResourceNotFoundException is handled here
        st.error(f"Error accessing AWS Secrets Manager. Check the secret name ('{secret_name}') and region ('{region_name}'): {e.response['Error']['Code']}")
        st.stop()
        return None

    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret)
        
        db_credentials = {
            'host': secret_dict.get(SECRET_KEYS['host_key']),
            'database': secret_dict.get(SECRET_KEYS['database_key']),
            'user': secret_dict.get(SECRET_KEYS['user_key']),
            'password': secret_dict.get(SECRET_KEYS['password_key'])
        }
        
        if all(db_credentials.values()):
            return db_credentials
        else:
            st.error("Error: Database credentials incomplete in Secrets Manager. Check the key names (DB_HOST, etc.).")
            st.stop()
            return None
    else:
        st.error("Error: Secret is not stored as a SecretString.")
        st.stop()
        return None

def get_mysql_connection():
    """Establishes a connection to the MySQL database."""
    credentials = get_secret()
    if not credentials:
        return None
        
    try:
        conn = mysql.connector.connect(
            host=credentials['host'],
            database=credentials['database'],
            user=credentials['user'],
            password=credentials['password']
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"MySQL Connection Error: Ensure the EC2 security group allows your IP/Streamlit server access to the RDS database (host: {credentials.get('host', 'N/A')}). Error: {err}")
        st.stop()
        return None

def fetch_upcoming_bookings():
    """Placeholder for conference room data (Firestore/other DB)."""
    return []

def fetch_all_users():
    """Placeholder for fetching user login data."""
    return {"testuser@zodopt.com": {"password": "password123", "dept": "IT"}}

def fetch_all_recent_visitor_logs():
    """Fetches all 'In Office' and recent 'Signed Out' visitor logs."""
    conn = get_mysql_connection()
    if conn is None:
        return []

    TABLE_NAME = 'visitor_log' 
    today = datetime.now().strftime('%Y-%m-%d')
    
    query = f"""
    SELECT 
        log_id, visitor_name, host, company, status, time_in_logic, time_out_logic 
    FROM {TABLE_NAME}
    WHERE status = 'In Office' 
    OR DATE(time_out_logic) = '{today}'
    ORDER BY time_in_logic DESC;
    """
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()
        
        # Post-process for display
        for log in result:
            # Convert DB fields to display format
            log['time_in_display'] = datetime.strptime(str(log['time_in_logic']), LOGIC_TIME_FORMAT).strftime(DISPLAY_TIME_FORMAT)
            
            # Handle time_out_logic
            time_out_str = str(log['time_out_logic']) if log['time_out_logic'] else ''
            if time_out_str:
                 log['time_out_display'] = datetime.strptime(time_out_str, LOGIC_TIME_FORMAT).strftime(DISPLAY_TIME_FORMAT)
            else:
                 log['time_out_display'] = '-'
                 
        return result
        
    except mysql.connector.Error as err:
        st.error(f"Error executing visitor log query: {err}")
        return []
    finally:
        if conn and conn.is_connected():
            conn.close()

def update_visitor_log_signout(log_id, time_out_logic):
    """Updates a visitor entry in the database with the sign-out time and status."""
    conn = get_mysql_connection()
    if conn is None:
        return False

    TABLE_NAME = 'visitor_log' 
    
    query = f"""
    UPDATE {TABLE_NAME}
    SET status = 'Signed Out', time_out_logic = %s
    WHERE log_id = %s
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, (time_out_logic, log_id))
        conn.commit()
        return True
        
    except mysql.connector.Error as err:
        st.error(f"Error updating visitor sign-out: {err}")
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()

# Placeholder for visitor.py to use (you'd need to implement the INSERT logic here)
def register_new_visitor(data):
    """Placeholder for inserting new visitor data into the database."""
    st.info("Registration simulated: Database connection logic is ready to execute INSERT.")
    return True


# ======================================================================
# --- 3. SESSION STATE INITIALIZATION & HELPERS ---
# ======================================================================

def initialize_app():
    """Initializes essential session state variables by loading current data from the database."""
    
    # 1. Main Navigation State
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'main' 
    
    # 2. Visitor Module State Initialization (Fetch real data)
    if 'visitor_log_data' not in st.session_state:
        st.session_state['visitor_log_data'] = fetch_all_recent_visitor_logs()
        
    # Additional Visitor Keys
    if 'visitor_form_step' not in st.session_state: st.session_state['visitor_form_step'] = 1
    if 'temp_visitor_data' not in st.session_state: st.session_state['temp_visitor_data'] = {}
    if 'registration_complete' not in st.session_state: st.session_state['registration_complete'] = False
    if 'last_registered_name' not in st.session_state: st.session_state['last_registered_name'] = 'Visitor'

    # 3. Conference Module State Initialization (Fetch placeholder data)
    if "bookings" not in st.session_state:
        st.session_state.bookings = fetch_upcoming_bookings()
        
    if "users" not in st.session_state:
        st.session_state.users = fetch_all_users() 
        
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "logged_in_user" not in st.session_state:
        st.session_state.logged_in_user = None

def set_background(image_path=None):
    """Sets the app background and applies custom CSS styling."""
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {BACKGROUND_COLOR} !important; min-height: 100vh !important; padding: 0 !important; margin: 0 !important; }}
        [data-testid="stAppViewContainer"] {{ padding: 0 !important; margin: 0 !important; background-color: transparent !important; }}
        [data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}
        .main .block-container {{ background-color: transparent !important; padding-top: 3rem; padding-bottom: 3rem; max-width: 100% !important; padding-left: 5rem; padding-right: 5rem; }}
        .log-card-container {{ background-color: {CONTENT_CARD_COLOR} !important; border-radius: 12px; padding: 20px; margin-bottom: 2rem; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border: 1px solid #e0e0e0; }}
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText, div[data-testid="stCaption"] {{ color: #1f1f1f !important; text-shadow: none; }}
        .main-title {{ color: #1a1a2e; font-size: 2.5rem; font-weight: 700; margin-bottom: 1rem; text-shadow: none; }}
        .nav-card-button {{ background-color: {CONTENT_CARD_COLOR}; border-radius: 12px; padding: 30px; text-align: center; transition: all 0.3s ease; cursor: pointer; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1); height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; border: 1px solid #e0e0e0; }}
        .nav-card-button:hover {{ transform: translateY(-5px); box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15); }}
        .icon-circle-box {{ width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 15px; color: white; }}
        .icon-vistplan {{ background: linear-gradient(135deg, {PURPLE_PRIMARY}, #9370DB); box-shadow: 0 5px 10px rgba(123, 104, 238, 0.4); }}
        .icon-conference {{ background: linear-gradient(135deg, {GREEN_PRIMARY}, #66CDAA); box-shadow: 0 5px 10px rgba(60, 179, 113, 0.4); }}
        .card-icon {{ font-size: 2.5rem; line-height: 1; }}
        .card-title {{ font-size: 1.25rem; font-weight: 600; color: #333; margin-bottom: 8px; }}
        .card-underline {{ width: 40px; height: 3px; border-radius: 2px; margin-top: 5px; }}
        .underline-vistplan {{ background-color: {PURPLE_PRIMARY}; }}
        .underline-conference {{ background-color: {GREEN_PRIMARY}; }}
        div[data-testid="stButton-nav_btn_visitor"], div[data-testid="stButton-nav_btn_conference"] {{ position: absolute; left: -5000px; top: -5000px; z-index: -1; width: 1px; height: 1px; overflow: hidden; }}
        [data-testid="stColumn"] {{ height: 100%; }}
        [data-testid="stMetric"] {{ background-color: {CONTENT_CARD_COLOR}; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); border: 1px solid #e0e0e0; }}
        </style>
    """, unsafe_allow_html=True)

def render_header_and_navigation():
    """Renders the ZODOPT title, logo, and the clickable navigation cards."""
    
    col_title, col_logo = st.columns([9, 1])
    
    with col_title:
        st.markdown('<h1 class="main-title">ZODOPT</h1>', unsafe_allow_html=True)
    
    with col_logo:
        try:
            logo_img = Image.open(LOGO_PATH)
            st.image(logo_img, width=80) 
        except Exception:
            st.markdown(f'<div style="width: 80px; height: 80px; background-color: #f0f0f0; border-radius: 8px; text-align: center; line-height: 80px;">LOGO</div>', unsafe_allow_html=True)
    
    st.container()
    nav_cols = st.columns(2)
    
    # --- VISTPLAN CARD ---
    with nav_cols[0]:
        st.markdown(
            f"""<div class="nav-card-button" onclick="document.getElementById('nav_btn_visitor').click()">
                <div class="icon-circle-box icon-vistplan"><span class="card-icon">📋</span></div>
                <div class="card-title">Vistplan</div>
                <div class="card-underline underline-vistplan"></div>
            </div>""", unsafe_allow_html=True
        )

    # --- CONFERENCE BOOKING CARD ---
    with nav_cols[1]:
        st.markdown(
            f"""<div class="nav-card-button" onclick="document.getElementById('nav_btn_conference').click()">
                <div class="icon-circle-box icon-conference"><span class="card-icon">🗓️</span></div>
                <div class="card-title">Conference Booking</div>
                <div class="card-underline underline-conference"></div>
            </div>""", unsafe_allow_html=True
        )
        
    # --- HIDDEN STREAMLIT BUTTONS ---
    if st.button('Vistplan (Hidden)', key="nav_btn_visitor", use_container_width=True):
        st.session_state['current_page'] = 'visitor'
        st.rerun()

    if st.button('Conference Room (Hidden)', key="nav_btn_conference", use_container_width=True):
        st.session_state['current_page'] = 'conference'
        st.session_state['page'] = 'login' 
        st.rerun()

def sign_out_visitor(log_id_to_update):
    """
    Updates the visitor_log table entry and refreshes the dashboard data.
    """
    try:
        current_time_logic = datetime.now().strftime(LOGIC_TIME_FORMAT)
        
        # 1. Update the MySQL database table using the integrated function
        success = update_visitor_log_signout(log_id_to_update, current_time_logic)

        if success:
            # 2. Reload the data to refresh the dashboard
            st.session_state['visitor_log_data'] = fetch_all_recent_visitor_logs()

            signed_out_log = next((log for log in st.session_state['visitor_log_data'] if log.get('log_id') == log_id_to_update), None)
            signed_out_name = signed_out_log.get('visitor_name', 'Visitor') if signed_out_log else 'Visitor'
                
            st.toast(f"Visitor '{signed_out_name}' signed out successfully!")
            st.rerun()
            
    except Exception as e:
        st.error(f"Error signing out visitor (ID: {log_id_to_update}).")
        st.exception(e)

def main_dashboard_content():
    """Renders the main dashboard content with metrics and side-by-side logs."""
    
    visitor_log = st.session_state['visitor_log_data'] 
    bookings_list = st.session_state['bookings'] 
    
    if visitor_log and isinstance(visitor_log, list) and visitor_log:
        log_df = pd.DataFrame(visitor_log)
    else:
        # Define necessary columns for an empty DataFrame to prevent errors
        log_df = pd.DataFrame(columns=['log_id', 'visitor_name', 'host', 'company', 'status', 'time_in_logic', 'time_out_logic', 'time_in_display', 'time_out_display'])
        
    current_visitors_df = log_df[log_df['status'] == 'In Office'] if not log_df.empty and 'status' in log_df.columns else pd.DataFrame()
    booking_df = pd.DataFrame(bookings_list) if bookings_list else pd.DataFrame()
    
    # --- Data Processing (Bookings) ---
    if not booking_df.empty and 'end' in booking_df.columns and 'start' in booking_df.columns:
        if 'dept' in booking_df.columns:
            booking_df = booking_df.rename(columns={'dept': 'Department'})
        
        now = datetime.now()
        booking_df['start'] = pd.to_datetime(booking_df['start'], errors='coerce')
        booking_df['end'] = pd.to_datetime(booking_df['end'], errors='coerce')
        
        booking_df = booking_df[
            booking_df['end'].dt.tz_localize(None) > now 
        ].sort_values(by='start').reset_index(drop=True)
    else:
        booking_df = pd.DataFrame() 

    # --- Metrics Section ---
    st.markdown("---") 
    col1, col2, col3 = st.columns(3) 
    
    with col1:
        st.metric(label="👥 Currently Signed In", value=len(current_visitors_df), delta_color='off')

    with col2:
        st.metric(label="🗓️ Total Upcoming Bookings", value=len(booking_df), delta_color='off')
        
    with col3:
        total_check_ins_today = 0
        if not log_df.empty and 'time_in_logic' in log_df.columns:
            log_df['Time In DT'] = pd.to_datetime(log_df['time_in_logic'], errors='coerce')
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
                # Sorting logic to ensure 'In Office' appears first
                if 'time_in_logic' in log_df.columns and 'status' in log_df.columns:
                    log_df['sort_key'] = log_df['status'].apply(lambda x: 0 if x == 'In Office' else 1)
                    display_df = log_df.sort_values(by=['sort_key', 'time_in_logic'], ascending=[True, False]).reset_index(drop=True).copy()
                else:
                    display_df = log_df.copy()

                col_spec = [1.5, 2.5, 2, 2, 1.5, 1.5, 1.5] 
                cols_header = st.columns(col_spec)
                
                # Column headers matching the data keys
                for c, name in zip(cols_header, ["Time In", "Name", "Host", "Company", "Status", "Time Out", "Action"]):
                    c.markdown(f"**{name}**")
                    
                st.markdown('<hr style="margin: 0.5rem 0 0.5rem 0; border-top: 1px solid #ddd;">', unsafe_allow_html=True)
                
                for i in range(len(display_df)):
                    row = display_df.iloc[i]
                    log_primary_key = row['log_id'] 
                    
                    cols = st.columns(col_spec)
                    
                    # Display data comes from the processed fields
                    cols[0].write(row['time_in_display'])
                    cols[1].write(row['visitor_name'])
                    cols[2].write(row['host'])
                    cols[3].write(row['company'])
                    
                    if row['status'] == 'In Office':
                        cols[4].markdown(f"**<span style='color:green;'>{row['status']}</span>**", unsafe_allow_html=True) 
                    else:
                        cols[4].write(row['status'])
                        
                    cols[5].write(row['time_out_display'])
                    
                    with cols[6]:
                        if row['status'] == 'In Office':
                            if st.button("🚪 Sign Out", key=f"sign_out_{log_primary_key}", use_container_width=True, type='primary'):
                                sign_out_visitor(log_primary_key)
                        else:
                            st.markdown("<div style='text-align:center;'>✅</div>", unsafe_allow_html=True)
                            
            except KeyError as e:
                st.error(f"Data column missing from the database. Check the column names in the fetch query: {e}")
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


# ======================================================================
# --- 4. MAIN EXECUTION LOOP ---
# ======================================================================

def main():
    initialize_app()
    set_background() 
    
    current_page = st.session_state.get('current_page', 'main')

    if current_page == 'main':
        render_header_and_navigation() 
        main_dashboard_content() 
        
    elif current_page == 'visitor':
        visitor_page()
        
    elif current_page == 'conference':
        conference_page()
        
    else:
        st.error("Navigation error: Unknown page requested. Returning to Dashboard.")
        st.session_state['current_page'] = 'main'
        st.rerun()

if __name__ == '__main__':
    main()
