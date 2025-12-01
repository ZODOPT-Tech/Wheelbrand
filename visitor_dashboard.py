import streamlit as st
import mysql.connector
import pandas as pd
from mysql.connector import Error
import json
import boto3
import traceback
from time import sleep

# ==============================================================================
# 1. CONFIGURATION & CREDENTIALS (Must match visitor_login.py)
# ==============================================================================
AWS_REGION = "ap-south-1" 
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS" 
DEFAULT_DB_PORT = 3306

@st.cache_resource
def get_db_credentials():
    """Loads DB credentials from AWS Secrets Manager or st.secrets fallback."""
    try:
        # Fallback to local Streamlit secrets 
        return {
            "DB_HOST": st.secrets["mysql_db"]["host"],
            "DB_NAME": st.secrets["mysql_db"]["database"],
            "DB_USER": st.secrets["mysql_db"]["user"],
            "DB_PASSWORD": st.secrets["mysql_db"]["password"],
        }
    except KeyError:
        st.error("FATAL: Database credentials not found in st.secrets['mysql_db'].")
        st.stop()
    except Exception as e:
        st.error(f"FATAL: Error retrieving credentials: {e}")
        st.stop()


@st.cache_resource
def get_fast_connection():
    """Returns a persistent MySQL connection object (cached by Streamlit)."""
    credentials = get_db_credentials()
    
    try:
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
    except mysql.connector.Error as err:
        st.error(f"FATAL: Dashboard DB Connection Error: {err.msg}")
        st.stop()

# ==============================================================================
# 2. DB INTERACTION FUNCTION
# ==============================================================================

def get_company_visitors(conn, company_id):
    """Fetches all visitor details for a specific company ID."""
    cursor = conn.cursor(dictionary=True)
    # Only select relevant, displayable columns
    query = """
    SELECT 
        registration_timestamp, full_name, email, phone_number,
        person_to_meet, purpose, from_company, has_laptop
    FROM visitors
    WHERE company_id = %s
    ORDER BY registration_timestamp DESC;
    """
    try:
        cursor.execute(query, (company_id,))
        return cursor.fetchall()
    except Exception as e:
        st.error(f"DB Error fetching visitor data: {e}")
        return []
    finally:
        cursor.close()

# ==============================================================================
# 3. STREAMLIT RENDERING
# ==============================================================================

def render_dashboard():
    """
    Renders the main dashboard for a logged-in Admin, displaying company-specific visitor data.
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
    
    conn = get_fast_connection()

    st.header(f"📊 {company_name} - Visitor Dashboard")
    st.markdown("---")

    st.markdown(f"## 👋 Welcome Back, **{admin_name}**")
    st.info(f"Displaying visitor records for Company ID: **{company_id}**")
    st.markdown('<div style="margin-bottom: 30px;"></div>', unsafe_allow_html=True)

    # --- Visitor Data Section ---
    st.subheader("Recent Visitor Check-Ins")
    
    # Fetch data specific to the logged-in company
    visitor_records = get_company_visitors(conn, company_id)

    if visitor_records:
        df = pd.DataFrame(visitor_records)
        
        # Format the timestamp for better readability
        df['Date/Time'] = pd.to_datetime(df['registration_timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        df['Laptop'] = df['has_laptop'].apply(lambda x: '✅' if x else '❌')
        
        # Rename columns for display
        df = df.rename(columns={
            'full_name': 'Visitor Name',
            'phone_number': 'Phone',
            'person_to_meet': 'Meeting Staff',
            'from_company': 'From Company',
            'purpose': 'Purpose'
        })
        
        # Select and order final columns
        display_cols = ['Date/Time', 'Visitor Name', 'Phone', 'Email', 'Meeting Staff', 'Purpose', 'From Company', 'Laptop']
        
        # Use Streamlit's data table feature
        st.dataframe(df[display_cols], use_container_width=True)
    else:
        st.warning("No visitor records found for this company.")
        
    st.markdown("---")
    
    # --- Navigation Controls ---
    col_new, col_logout = st.columns([2, 1])

    with col_new:
        if st.button("➕ Register New Visitor", type="primary", use_container_width=True):
            # Navigates to the 'visitor_details' page to start registration
            st.session_state['current_page'] = 'visitor_details'
            st.rerun()

    with col_logout:
        if st.button("← Admin Logout", key="admin_dashboard_logout_btn", use_container_width=True):
            # Clear all Admin session state data
            for key in ['admin_logged_in', 'admin_id', 'admin_email', 'admin_name', 'company_id', 'company_name']:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Navigate back to the login page and ensure the auth view resets
            st.session_state['current_page'] = 'visitor_login'
            if 'visitor_auth_view' in st.session_state:
                del st.session_state['visitor_auth_view']
                
            st.rerun()
