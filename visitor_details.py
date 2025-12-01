import streamlit as st
import mysql.connector
import pandas as pd
from mysql.connector import Error
import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import traceback

# NOTE: The get_db_credentials and get_fast_connection functions are copied 
# here for self-contained functionality, assuming this file is the main entry point.
# ==============================================================================
# 1. CONFIGURATION & CREDENTIALS (AWS Integration) - COPIED FROM DASHBOARD
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
    """Returns a persistent MySQL connection object."""
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
        return None
    except Error as err:
        st.error(f"FATAL: MySQL Connection Error: Cannot connect. Details: {err.msg}")
        st.stop()
    except Exception as e:
        st.error(f"FATAL: Unexpected Connection Error: {e}")
        st.stop()


# ==============================================================================
# 2. DB INTERACTION FUNCTION: SAVE NEW VISITOR
# ==============================================================================

def save_visitor_details(conn, data):
    """
    Saves new visitor details into the 'visitors' table.
    The 'checkout_time' column is omitted, defaulting to NULL (checked in).
    """
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Ensure company_id is available in the session state
        company_id = st.session_state.get('company_id')
        if not company_id:
            st.error("Missing Company ID for registration. Cannot save visitor.")
            return False

        # SQL Query updated to include company_id and registration_timestamp
        sql = """
        INSERT INTO visitors (
            company_id, registration_timestamp, full_name, phone_number, email, 
            person_to_meet, purpose, from_company, has_laptop
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Prepare data tuple
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        values = (
            company_id,
            current_timestamp,
            data['full_name'],
            data['phone_number'],
            data['email'],
            data['person_to_meet'],
            data['purpose'],
            data['from_company'],
            data['has_laptop']
        )
        
        cursor.execute(sql, values)
        conn.commit()
        st.success(f"✅ Visitor '{data['full_name']}' checked in successfully!")
        return True
        
    except Error as e:
        st.error(f"Database Error: Could not save visitor details. {e}")
        conn.rollback()
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred during save: {e}")
        return False
    finally:
        if cursor:
            cursor.close()

# ==============================================================================
# 3. STREAMLIT RENDERING: VISITOR FORM
# ==============================================================================

def render_visitor_details_form():
    """Renders the visitor registration form."""
    
    # Check required session state variables
    if not st.session_state.get('admin_logged_in'):
        st.warning("Please log in as Admin to access registration.")
        st.session_state['current_page'] = 'visitor_login'
        st.rerun()
        return

    conn = get_fast_connection()
    if conn is None:
        return # Error already displayed by get_fast_connection

    st.header("📋 New Visitor Check-In")
    st.markdown("Please fill out the details below to register the visitor.")

    with st.form(key='visitor_form'):
        
        st.subheader("Visitor Contact Information")
        full_name = st.text_input("Full Name *", key='full_name', placeholder="John Doe")
        phone_number = st.text_input("Phone Number *", key='phone_number', placeholder="9876543210")
        email = st.text_input("Email (Optional)", key='email', placeholder="john.doe@example.com")
        from_company = st.text_input("Company/Organization *", key='from_company', placeholder="Tech Innovations Inc.")
        
        st.subheader("Visit Details")
        person_to_meet = st.text_input("Person to Meet *", key='person_to_meet', placeholder="Jane Smith")
        purpose = st.selectbox(
            "Purpose of Visit *", 
            options=['Meeting', 'Interview', 'Delivery', 'Maintenance', 'Other'],
            key='purpose'
        )
        has_laptop = st.checkbox("Is the visitor carrying a laptop/device?", key='has_laptop')

        st.markdown("---")
        submit_button = st.form_submit_button("✅ Check In Visitor", type="primary")

        if submit_button:
            # 1. Validation
            if not full_name or not phone_number or not person_to_meet or not from_company:
                st.error("Please fill in all fields marked with an asterisk (*).")
            else:
                # 2. Collect Data
                visitor_data = {
                    'full_name': full_name,
                    'phone_number': phone_number,
                    'email': email,
                    'from_company': from_company,
                    'person_to_meet': person_to_meet,
                    'purpose': purpose,
                    'has_laptop': has_laptop
                }
                
                # 3. Save to DB
                if save_visitor_details(conn, visitor_data):
                    # Clear inputs (optional) and redirect to dashboard
                    # This requires resetting the form, which st.rerun handles implicitly after a successful save.
                    
                    # Redirect back to the dashboard
                    st.session_state['current_page'] = 'visitor_dashboard'
                    st.rerun()


    # --- Back Button ---
    if st.button("← Back to Dashboard", key="back_to_dashboard_btn"):
        st.session_state['current_page'] = 'visitor_dashboard'
        st.rerun()

# If running this file directly (for testing)
if __name__ == "__main__":
    if 'admin_logged_in' not in st.session_state:
        st.session_state['admin_logged_in'] = True
        st.session_state['company_id'] = 1 # Required for saving records
    
    render_visitor_details_form()
