import streamlit as st
import mysql.connector
import pandas as pd
from mysql.connector import Error
import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import traceback
from time import sleep

# ==============================================================================
# 1. CONFIGURATION & CREDENTIALS (AWS Integration)
# ==============================================================================

# NOTE: Ensure these values exactly match your AWS Secrets Manager setup.
AWS_REGION = "ap-south-1" 
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS" 
DEFAULT_DB_PORT = 3306

@st.cache_resource(ttl=3600) 
def get_db_credentials():
    """Retrieves database credentials ONLY from AWS Secrets Manager."""
    
    st.info("Attempting to retrieve DB credentials from AWS Secrets Manager...")
    
    try:
        # Boto3 automatically uses the EC2 Instance Profile credentials
        client = boto3.client('secretsmanager', region_name=AWS_REGION)
        
        get_secret_value_response = client.get_secret_value(
            SecretId=AWS_SECRET_NAME
        )
        
        if 'SecretString' not in get_secret_value_response:
            raise ValueError("SecretString is missing in the AWS response.")
            
        secret = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret)
        
        # Verify and return the dictionary structure
        required_keys = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        if not all(key in secret_dict for key in required_keys):
            raise KeyError("Missing required DB keys (DB_HOST, DB_NAME, etc.) in the AWS secret.")

        st.success("Successfully retrieved DB credentials from AWS.")
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
    Returns a persistent MySQL connection object by fetching credentials from AWS.
    This function will now halt the app if credential retrieval fails.
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
        return conn
    except EnvironmentError:
        # st.stop() is handled inside get_db_credentials if it raises EnvironmentError
        return None
    except Error as err:
        error_msg = f"FATAL: MySQL Connection Error: Cannot connect. Details: {err.msg}"
        st.error(error_msg)
        st.stop()
    except Exception as e:
        error_msg = f"FATAL: Unexpected Connection Error: {e}"
        st.error(error_msg)
        st.stop()

# ==============================================================================
# 2. DB INTERACTION FUNCTIONS (UPDATED)
# ==============================================================================

def update_checkout_time(conn, visitor_id):
    """Updates the checkout_time for a specific visitor in the database."""
    cursor = None
    try:
        cursor = conn.cursor()
        sql = "UPDATE visitors SET checkout_time = %s WHERE id = %s"
        checkout_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute(sql, (checkout_time, visitor_id))
        conn.commit()
        st.success(f"Visitor ID {visitor_id} checked out successfully.")
        return True
        
    except Error as e:
        st.error(f"Database Error: Could not update checkout time for ID {visitor_id}. {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()

def get_company_visitors(conn, company_id):
    """
    Fetches visitor details for a specific company ID, including records from the 
    previous and present day (last 48 hours), ordered by recent check-in.
    """
    cursor = None
    try:
        # Filter for the last 48 hours to capture 'present day' and 'previous day'
        two_days_ago = (datetime.now() - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')

        cursor = conn.cursor(dictionary=True)
        query = f"""
        SELECT 
            id, registration_timestamp, full_name, email, phone_number,
            person_to_meet, purpose, from_company, has_laptop, checkout_time
        FROM visitors
        WHERE company_id = %s AND registration_timestamp >= %s
        ORDER BY registration_timestamp DESC;
        """
        
        cursor.execute(query, (company_id, two_days_ago))
        return cursor.fetchall()
    except Exception as e:
        st.error(f"DB Error fetching visitor data: {e}")
        return []
    finally:
        if cursor:
            cursor.close()

# ==============================================================================
# 3. STREAMLIT RENDERING (UPDATED)
# ==============================================================================

def render_dashboard():
    """
    Renders the main dashboard for a logged-in Admin, displaying company-specific visitor data 
    with checkout functionality.
    """
    # 1. Enforce Admin Login State
    if not st.session_state.get('admin_logged_in'):
        st.warning("Please log in to view the dashboard.")
        st.session_state['current_page'] = 'visitor_login'
        st.rerun()
        return

    company_name = st.session_state.get('company_name', 'Company Dashboard')
    admin_name = st.session_state.get('admin_name', 'Admin')
    company_id = st.session_state.get('company_id')
    
    if not company_id:
        st.error("Admin session is missing Company ID. Please log in again.")
        st.session_state['current_page'] = 'visitor_login'
        st.rerun()
        return

    # Attempt to get the database connection
    conn = get_fast_connection()
    if conn is None:
        # Connection failure is handled inside get_fast_connection with st.stop() or st.error()
        return

    st.header(f"📊 {company_name} - Visitor Dashboard")
    st.markdown("---")

    st.markdown(f"## 👋 Welcome Back, **{admin_name}**")
    st.info(f"Displaying visitor records for Company ID: **{company_id}**")
    st.markdown('<div style="margin-bottom: 30px;"></div>', unsafe_allow_html=True)

    # --- Visitor Data Section ---
    st.subheader("Recent Visitor Check-Ins")
    
    # Fetch data specific to the logged-in company (filtered by date)
    visitor_records = get_company_visitors(conn, company_id)

    if visitor_records:
        df = pd.DataFrame(visitor_records)
        
        # 1. Calculate Status
        df['Status'] = df['checkout_time'].apply(
            lambda x: 'CHECKED OUT' if pd.notna(x) else 'CHECKED IN'
        )
        
        # 2. Data formatting
        # Ensure timestamp is formatted for display
        df['Date/Time'] = pd.to_datetime(df['registration_timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        df['Laptop'] = df['has_laptop'].apply(lambda x: '✅' if x else '❌')
        
        # Keep 'id' for checkout logic, but rename others
        df = df.rename(columns={
            'full_name': 'Visitor Name',
            'phone_number': 'Phone',
            'person_to_meet': 'Meeting Staff',
            'from_company': 'From Company',
            'purpose': 'Purpose',
            'email': 'Email'
        })
        
        # Select final columns for display
        display_cols = ['Date/Time', 'Visitor Name', 'Phone', 'Email', 'Meeting Staff', 'Purpose', 'From Company', 'Laptop', 'Status']
        
        # 3. Sequential Index (Starts from 1)
        df_display = df[display_cols].copy()
        df_display.reset_index(drop=True, inplace=True)
        df_display.index = df_display.index + 1
        
        st.dataframe(df_display, use_container_width=True)

        # 4. Checkout UI
        st.markdown("---")
        st.subheader("Visitor Checkout 🚪")
        
        checkout_visitors = df[df['Status'] == 'CHECKED IN']
        
        if not checkout_visitors.empty:
            
            # Create a dictionary for easy selection: Display Name (ID) -> Actual ID
            checkout_options = {
                f"{row['Visitor Name']} ({row['From Company']}) - In: {row['Date/Time']}": row['id']
                for index, row in checkout_visitors.iterrows()
            }
            
            with st.form("checkout_form"):
                
                visitor_key = st.selectbox(
                    "Select Visitor to Check Out:",
                    options=list(checkout_options.keys()),
                    key="visitor_to_checkout_key"
                )
                
                checkout_submitted = st.form_submit_button("👋 Check Out Visitor", type="secondary")
                
                if checkout_submitted and visitor_key:
                    visitor_id = checkout_options[visitor_key]
                    if update_checkout_time(conn, visitor_id):
                        st.rerun() # Refresh dashboard on successful checkout
        else:
            st.info("All visitors currently displayed are checked out.")
            
    else:
        st.warning("No visitor records found for this company in the last 48 hours.")
        
    st.markdown("---")
    
    # --- Navigation Controls ---
    col_new, col_logout = st.columns([2, 1])

    with col_new:
        if st.button("➕ Register New Visitor", type="primary", use_container_width=True):
            st.session_state['current_page'] = 'visitor_details'
            st.session_state['registration_step'] = 'primary'
            st.session_state['visitor_data'] = {}
            st.rerun()

    with col_logout:
        if st.button("← Admin Logout", key="admin_dashboard_logout_btn", use_container_width=True):
            # Clear all Admin session state data
            for key in ['admin_logged_in', 'admin_id', 'admin_email', 'admin_name', 'company_id', 'company_name']:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.session_state['current_page'] = 'visitor_login'
            if 'visitor_auth_view' in st.session_state:
                del st.session_state['visitor_auth_view']
                
            st.rerun()

# If running this file directly (for testing)
if __name__ == "__main__":
    if 'admin_logged_in' not in st.session_state:
        st.session_state['admin_logged_in'] = True
        st.session_state['admin_name'] = "Test Admin"
        st.session_state['company_id'] = 1  # Use a valid test company ID
        st.session_state['company_name'] = "Test Corp"
    
    render_dashboard()
