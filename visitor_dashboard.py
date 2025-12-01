import streamlit as st
import mysql.connector
import pandas as pd
from mysql.connector import Error
import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import traceback

# ==============================================================================
# 1. CONFIGURATION & CREDENTIALS (AWS Integration)
# ==============================================================================

AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
DEFAULT_DB_PORT = 3306

@st.cache_resource(ttl=3600)
def get_db_credentials():
    """Retrieves database credentials ONLY from AWS Secrets Manager."""
    try:
        client = boto3.client('secretsmanager', region_name=AWS_REGION)
        get_secret_value_response = client.get_secret_value(
            SecretId=AWS_SECRET_NAME
        )
        secret = get_secret_value_response.get('SecretString')
        if not secret:
            raise ValueError("SecretString is missing in the AWS response.")
            
        secret_dict = json.loads(secret)
        required_keys = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        if not all(key in secret_dict for key in required_keys):
            raise KeyError("Missing required DB keys (DB_HOST, DB_NAME, etc.) in the AWS secret.")

        # st.success("Successfully retrieved DB credentials from AWS.")
        return {
            "DB_HOST": secret_dict["DB_HOST"],
            "DB_NAME": secret_dict["DB_NAME"],
            "DB_USER": secret_dict["DB_USER"],
            "DB_PASSWORD": secret_dict["DB_PASSWORD"],
        }
    except ClientError as e:
        error_msg = f"AWS Secrets Manager API Error ({e.response['Error']['Code']}): Check IAM Role and ARN."
        st.error(error_msg)
        raise EnvironmentError(error_msg)
    except Exception as e:
        error_msg = f"FATAL: Credential Retrieval Failure: {e}"
        st.error(error_msg)
        raise EnvironmentError(error_msg)

@st.cache_resource(ttl=None)
def get_fast_connection():
    """
    Returns a persistent MySQL connection object. 
    Pings the connection to ensure it's still alive.
    """
    try:
        credentials = get_db_credentials()
        conn = mysql.connector.connect(
            host=credentials["DB_HOST"],
            user=credentials["DB_USER"],
            password=credentials["DB_PASSWORD"],
            database=credentials["DB_NAME"],
            port=DEFAULT_DB_PORT,
            autocommit=True,
            connection_timeout=10,
        )
        # Check if connection is alive and auto-reconnect if configured
        if not conn.is_connected():
            conn.ping(reconnect=True) 
        
        return conn
    except EnvironmentError:
        return None # Error already displayed by get_db_credentials
    except Error as err:
        st.error(f"FATAL: MySQL Connection Error: Cannot connect. Details: {err.msg}")
        st.stop()
    except Exception as e:
        st.error(f"FATAL: Unexpected Connection Error: {e}")
        st.stop()

# ==============================================================================
# 2. DB INTERACTION FUNCTIONS: FETCH & CHECKOUT
# ==============================================================================

def fetch_current_visitors(conn, company_id):
    """
    Fetches all visitor records for the given company_id who are currently checked in 
    (i.e., checkout_time IS NULL). Also fetches checked out visitors in the last 48 hours.
    """
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        # Calculate the cutoff time for recently checked-out visitors
        time_limit = datetime.now() - timedelta(hours=48)
        
        sql = """
        SELECT 
            visitor_id, registration_timestamp, full_name, phone_number, email, 
            purpose, person_to_meet, from_company, has_laptop, checkout_time
        FROM visitors 
        WHERE company_id = %s AND (checkout_time IS NULL OR registration_timestamp >= %s)
        ORDER BY registration_timestamp DESC;
        """
        cursor.execute(sql, (company_id, time_limit))
        records = cursor.fetchall()
        
        if not records:
            # st.info("No visitor records found for this company in the last 48 hours.")
            return pd.DataFrame() # Return empty DataFrame
            
        df = pd.DataFrame(records)
        df['status'] = df['checkout_time'].apply(lambda x: 'Checked Out' if x is not None else 'Checked In')
        return df

    except Error as e:
        st.error(f"DB Error fetching visitor data: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An unexpected error occurred during fetch: {e}")
        return pd.DataFrame()
    finally:
        if cursor:
            cursor.close()

def checkout_visitor(conn, visitor_id):
    """
    Updates the checkout_time for a specific visitor using their visitor_id.
    """
    cursor = None
    try:
        cursor = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        sql = """
        UPDATE visitors
        SET checkout_time = %s
        WHERE visitor_id = %s
        """
        cursor.execute(sql, (current_time, visitor_id))
        conn.commit()
        st.toast(f"Visitor ID {visitor_id} checked out successfully.", icon="🚪")
        return True
    except Error as e:
        st.error(f"DB Error during checkout: Could not update record for ID {visitor_id}. {e}")
        conn.rollback()
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred during checkout: {e}")
        return False
    finally:
        if cursor:
            cursor.close()

# ==============================================================================
# 3. STREAMLIT RENDERING: DASHBOARD
# ==============================================================================

def render_dashboard():
    """Renders the main dashboard interface for admins."""
    
    # 1. Authentication and Setup Check
    if not st.session_state.get('admin_logged_in'):
        st.warning("Please log in as Admin to view the dashboard.")
        st.session_state['current_page'] = 'visitor_login'
        st.rerun()
        return

    conn = get_fast_connection()
    if conn is None:
        return # Error already displayed by get_fast_connection

    company_id = st.session_state.get('company_id')
    
    st.title("🏛️ Visitor Management Dashboard")
    st.markdown(f"**Company ID:** `{company_id}`") # Display for identification

    # --- Top Buttons ---
    col_new, col_refresh = st.columns([1, 4])
    with col_new:
        if st.button("➕ New Check-In", type="primary"):
            # Set the state to navigate to the Check-in page (in the main app logic)
            st.session_state['current_page'] = 'details_page' 
            st.rerun()
    with col_refresh:
        # Refresh button to force data reload (clears cache for fetch function)
        st.button("🔄 Refresh Data", on_click=lambda: st.cache_data.clear(), help="Click to force a fresh data fetch from the database.")
        
    st.divider()
    st.header("Active & Recent Visitors")

    # 2. Fetch Data
    # st.cache_data is not used here to ensure dynamic updates on check-out/refresh button clicks
    visitor_data = fetch_current_visitors(conn, company_id)

    if visitor_data.empty:
        st.info("No visitor records found for this company in the last 48 hours.")
        return
        
    # Separate data into active and recent
    active_visitors = visitor_data[visitor_data['status'] == 'Checked In']
    recent_visitors = visitor_data[visitor_data['status'] == 'Checked Out']

    # --- Active Visitors Section ---
    st.subheader(f"🟢 Currently Checked In ({len(active_visitors)})")
    
    if active_visitors.empty:
        st.info("No visitors are currently checked in.")
    else:
        # Define headers outside the loop
        header_cols = st.columns([0.5, 2.5, 1.5, 1.5, 1.5])
        header_cols[0].markdown("**ID**")
        header_cols[1].markdown("**Visitor & Company**")
        header_cols[2].markdown("**Meeting**")
        header_cols[3].markdown("**Check-In Time**")
        header_cols[4].markdown("**Action**")
        
        st.markdown("---") # Separator after headers

        for index, row in active_visitors.iterrows():
            col_id, col_name, col_meet, col_time, col_button = st.columns([0.5, 2.5, 1.5, 1.5, 1.5])
            
            # Display basic info
            col_id.markdown(f"`{row['visitor_id']}`")
            col_name.markdown(f"**{row['full_name']}** ({row['from_company']})")

            # Purpose/Meeting Info
            tooltip_text = f"Purpose: {row['purpose']}"
            col_meet.markdown(f"**{row['person_to_meet']}** ℹ️", help=tooltip_text)
            
            # Time Info
            col_time.markdown(f"{row['registration_timestamp'].strftime('%I:%M %p, %b %d')}")
            
            # Check Out Button Logic
            with col_button:
                if st.button("🚪 Check Out", key=f"checkout_{row['visitor_id']}", type="secondary", use_container_width=True):
                    if checkout_visitor(conn, row['visitor_id']):
                        # Rerun to refresh the list and move the visitor to the 'Checked Out' section
                        st.rerun()
            st.divider()


    # --- Recent Visitors Section ---
    st.divider()
    with st.expander(f"🔵 Recently Checked Out (Last 48 Hours, {len(recent_visitors)})"):
        if recent_visitors.empty:
            st.info("No visitors checked out recently.")
        else:
            # Display recent visitors as a static table
            display_columns = ['visitor_id', 'full_name', 'from_company', 'person_to_meet', 
                               'registration_timestamp', 'checkout_time', 'purpose']
            
            # Format timestamps for display
            recent_visitors_display = recent_visitors[display_columns].copy()
            recent_visitors_display['registration_timestamp'] = recent_visitors_display['registration_timestamp'].dt.strftime('%b %d, %I:%M %p')
            recent_visitors_display['checkout_time'] = recent_visitors_display['checkout_time'].dt.strftime('%b %d, %I:%M %p')
            
            # Rename columns for clarity
            recent_visitors_display.columns = ['ID', 'Visitor Name', 'Company', 'Met Person', 
                                               'Check-In', 'Check-Out', 'Purpose']

            st.dataframe(
                recent_visitors_display, 
                use_container_width=True, 
                hide_index=True,
                column_order=['ID', 'Visitor Name', 'Company', 'Check-In', 'Check-Out', 'Met Person', 'Purpose']
            )


# --- Placeholder for Login/Routing ---
def render_login_page():
    st.title("Admin Login")
    st.markdown("Please use admin credentials to access the dashboard.")
    
    # Simple placeholder login for local testing
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Log In", type="primary"):
        # Dummy credentials for testing. Replace with actual authentication logic (e.g., hashed password check)
        if username == "admin" and password == "123": 
            st.session_state['admin_logged_in'] = True
            st.session_state['company_id'] = 1 # Set a dummy company ID
            st.session_state['current_page'] = 'visitor_dashboard'
            st.rerun()
        else:
            st.error("Invalid credentials.")

# --- Main App Logic ---
if __name__ == "__main__":
    # Ensure current_page is initialized and defaults to a known state
    if 'admin_logged_in' not in st.session_state:
        st.session_state['admin_logged_in'] = False
    if 'current_page' not in st.session_state or st.session_state['current_page'] == 'details_page':
        # Default to login if not logged in, otherwise default to dashboard
        if st.session_state['admin_logged_in']:
             st.session_state['current_page'] = 'visitor_dashboard'
        else:
             st.session_state['current_page'] = 'visitor_login'
             
    if 'company_id' not in st.session_state:
        st.session_state['company_id'] = 1 # Default for testing

    # Use a clear mapping for navigation
    if st.session_state['current_page'] == 'visitor_login':
        render_login_page()
    elif st.session_state['current_page'] == 'visitor_dashboard':
        render_dashboard()
    elif st.session_state['current_page'] == 'details_page':
         # This block handles the redirection request to the external check-in page
         st.info("Redirecting to the Check-In form in the 'visitor_details.py' page...")
         # Reset the state to dashboard to allow navigation back
         st.session_state['current_page'] = 'visitor_dashboard'
         # If this app were part of a multi-page Streamlit deployment, 'st.rerun()' 
         # would typically lead to the main app routing to the requested page.
         st.rerun() 
    else:
        # Default fallback
        st.session_state['current_page'] = 'visitor_dashboard'
        render_dashboard()
