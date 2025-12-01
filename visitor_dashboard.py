import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error

# --- ASSUMING THESE ARE IMPORTED FROM visitor_details.py ---
# from visitor_details import get_fast_connection 
# You need the get_fast_connection function available.
# -----------------------------------------------------------

def update_checkout_time(visitor_id):
    """Updates the checkout_time for a specific visitor in the database."""
    conn = None
    try:
        conn = st.session_state['db_connection'] # Use the cached connection
        if conn is None:
            st.error("Database connection not available.")
            return False
            
        cursor = conn.cursor()
        
        # We assume the table is named 'visitors' and has a 'checkout_time' column (see MySQL section)
        sql = "UPDATE visitors SET checkout_time = %s WHERE id = %s"
        checkout_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute(sql, (checkout_time, visitor_id))
        conn.commit()
        st.success(f"Visitor ID {visitor_id} checked out successfully.")
        return True
        
    except Error as e:
        st.error(f"Database Error: Could not update checkout time. {e}")
        return False
    finally:
        if cursor:
            cursor.close()

def fetch_recent_visitors():
    """Fetches visitors from the present day and the previous day (last 48 hours)."""
    conn = None
    try:
        conn = st.session_state['db_connection'] # Use the cached connection
        if conn is None:
            return pd.DataFrame()

        cursor = conn.cursor(dictionary=True)
        
        # Calculate time window: Last 48 hours is usually sufficient for "previous day"
        two_days_ago = (datetime.now() - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Select all relevant fields, including 'id' and 'checkout_time'
        query = f"""
        SELECT 
            id, registration_timestamp, full_name, phone_number, email, 
            person_to_meet, purpose, from_company, has_laptop, checkout_time
        FROM visitors
        WHERE registration_timestamp >= '{two_days_ago}'
        ORDER BY registration_timestamp DESC;
        """
        cursor.execute(query)
        records = cursor.fetchall()
        
        if not records:
            return pd.DataFrame()
            
        df = pd.DataFrame(records)
        return df

    except Error as e:
        st.error(f"Database Query Error: Could not fetch records. {e}")
        return pd.DataFrame()
    finally:
        if cursor:
            cursor.close()

def render_dashboard():
    """Renders the visitor dashboard with recent check-ins and the checkout button."""
    
    st.title("Recent Visitor Check-Ins 🗓️")
    
    # Ensure the connection is established and stored in session state
    if 'db_connection' not in st.session_state:
        # Assuming you call the connection function from visitor_details
        # Replace this with your actual connection setup if different
        try:
             # This line needs to be customized based on your actual file imports
            st.session_state['db_connection'] = get_fast_connection() 
        except Exception:
            st.warning("Failed to initialize database connection.")
            return
            
    # --- Fetch Data ---
    df = fetch_recent_visitors()
    
    if df.empty:
        st.info("No visitor check-ins found in the last 48 hours.")
    else:
        # --- Pre-processing for Display ---
        
        # 1. Format Time
        df['Date/Time'] = df['registration_timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        
        # 2. Format Boolean/Laptop
        df['Laptop'] = df['has_laptop'].apply(lambda x: '✅' if x else '❌')
        
        # 3. Handle Status and Checkout Button
        df['Status'] = df['checkout_time'].apply(
            lambda x: 'CHECKED OUT' if pd.notna(x) else 'CHECKED IN'
        )
        
        # Select and Rename Columns for Dashboard Display
        df_display = df[[
            'id', 'Date/Time', 'full_name', 'phone_number', 'email', 
            'person_to_meet', 'purpose', 'from_company', 'Laptop', 'Status'
        ]]
        
        df_display = df_display.rename(columns={
            'full_name': 'Visitor Name',
            'phone_number': 'Phone',
            'person_to_meet': 'Meeting Staff',
            'from_company': 'From Company'
        })
        
        # 4. Sequential Index (Starting from 1)
        df_display = df_display.reset_index(drop=True)
        df_display.index = df_display.index + 1
        
        # --- Display Table ---
        st.dataframe(df_display.drop(columns=['id']), use_container_width=True)
        
        st.markdown("---")
        st.subheader("Visitor Checkout 🚪")
        
        # --- Checkout Form/Logic ---
        checkout_visitors = df[df['Status'] == 'CHECKED IN']
        
        if not checkout_visitors.empty:
            
            # Create a dictionary for easy selection
            checkout_options = {
                f"{row['full_name']} (ID: {row['id']}) - In: {row['Date/Time']}": row['id']
                for index, row in checkout_visitors.iterrows()
            }
            
            with st.form("checkout_form"):
                
                # Dropdown to select only currently checked-in visitors
                visitor_key = st.selectbox(
                    "Select Visitor to Check Out:",
                    options=list(checkout_options.keys()),
                    key="visitor_to_checkout_key"
                )
                
                # Check for submission
                checkout_submitted = st.form_submit_button("👋 Check Out Visitor")
                
                if checkout_submitted and visitor_key:
                    visitor_id = checkout_options[visitor_key]
                    if update_checkout_time(visitor_id):
                        # Force a re-run to update the table display
                        st.rerun() 
        else:
            st.info("All visitors are currently checked out.")

    # --- Buttons ---
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Your existing 'Register New Visitor' button logic
        if st.button("✨ Register New Visitor", use_container_width=True, type="primary"):
            st.session_state['current_page'] = 'visitor_details'
            st.session_state['registration_step'] = 'primary'
            st.session_state['visitor_data'] = {}
            st.rerun()

    with col2:
        # Your existing 'Admin Logout' button logic
        if st.button("← Admin Logout", use_container_width=True):
            st.session_state['admin_logged_in'] = False
            st.session_state['current_page'] = 'visitor_login'
            st.rerun()

# --- You would call render_dashboard() from your main app structure ---
# if st.session_state.get('current_page') == 'visitor_dashboard':
#     render_dashboard()
