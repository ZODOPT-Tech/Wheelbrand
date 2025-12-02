import streamlit as st
from datetime import datetime
import json
import boto3
from botocore.exceptions import ClientError
import mysql.connector
from mysql.connector import Error

# ==============================================================================
# 1. AWS CONFIG + DB CONNECTION
# ==============================================================================

AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS" 
DEFAULT_DB_PORT = 3306

@st.cache_resource(ttl=3600)
def get_db_credentials():
    try:
        client = boto3.client('secretsmanager', region_name=AWS_REGION)
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        secret_dict = json.loads(resp['SecretString'])

        return {
            "DB_HOST": secret_dict["DB_HOST"],
            "DB_NAME": secret_dict["DB_NAME"],
            "DB_USER": secret_dict["DB_USER"],
            "DB_PASSWORD": secret_dict["DB_PASSWORD"],
        }
    except Exception as e:
        st.error(f"Cannot load DB credentials: {e}")
        st.stop()

@st.cache_resource
def get_fast_connection():
    try:
        creds = get_db_credentials()
        return mysql.connector.connect(
            host=creds["DB_HOST"],
            user=creds["DB_USER"],
            password=creds["DB_PASSWORD"],
            database=creds["DB_NAME"],
            port=DEFAULT_DB_PORT,
            autocommit=True,
        )
    except Exception as e:
        st.error(f"DB Connection Error: {e}")
        st.stop()


# ==============================================================================
# 2. STATE INITIALIZATION
# ==============================================================================

def initialize_state():
    if "visitor_step" not in st.session_state:
        st.session_state["visitor_step"] = "primary"
    if "visitor_info" not in st.session_state:
        st.session_state["visitor_info"] = {}

    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    if "company_id" not in st.session_state:
        st.session_state["company_id"] = None


# ==============================================================================
# 3. SAVE VISITOR DATA
# ==============================================================================

def save_visitor_to_db(data):
    conn = get_fast_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO visitors (
        company_id, registration_timestamp, full_name, phone_number, email,
        visit_type, purpose, person_to_meet, gender
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    values = (
        st.session_state["company_id"],
        datetime.now(),
        data["name"],
        data["phone"],
        data["email"],
        data["visit_type"],
        data["purpose"],
        data["person_to_meet"],
        data["gender"],
    )

    try:
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        st.error(f"DB Error: {e}")
        return False


# ==============================================================================
# 4. CUSTOM CSS + HEADER
# ==============================================================================

def apply_styles():
    st.markdown("""
    <style>
        .header-box {
            background: linear-gradient(90deg, #4B2ECF, #7A42FF);
            padding: 22px 35px;
            color: white;
            border-radius: 10px;
            font-size: 28px;
            font-weight: 800;
            margin-bottom: 25px;
        }
        .step-tabs {
            display: flex;
            gap: 20px;
            margin-bottom: 25px;
            font-weight: 600;
        }
        .step-active {
            color: #4B2ECF;
            border-bottom: 3px solid #4B2ECF;
            padding-bottom: 5px;
        }
        .step-inactive {
            color: #999;
        }
        div.stButton > button {
            background: #4B2ECF !important;
            color: white !important;
            padding: 14px 0;
            font-size: 18px;
            border-radius: 10px;
            border: none;
        }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    company_id = st.session_state.get("company_id", "N/A")

    st.markdown(
        f"""
        <div class="header-box">
            VISITOR REGISTRATION — Company ID: {company_id}
        </div>
        """,
        unsafe_allow_html=True
    )

    step = st.session_state["visitor_step"]

    st.markdown(
        f"""
        <div class="step-tabs">
            <div class="{ 'step-active' if step=='primary' else 'step-inactive' }">1. Primary Details</div>
            <div class="{ 'step-active' if step=='secondary' else 'step-inactive' }">2. Visit Details</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ==============================================================================
# 5. PRIMARY DETAILS FORM
# ==============================================================================

def render_primary_details():
    st.markdown("### Visitor Contact Details")

    with st.form("primary_form"):
        name = st.text_input("Full Name *", st.session_state["visitor_info"].get("name", ""))
        phone = st.text_input("Phone Number *", st.session_state["visitor_info"].get("phone", ""))
        email = st.text_input("Email *", st.session_state["visitor_info"].get("email", ""))

        submitted = st.form_submit_button("Next →")

        if submitted:
            if not name or not phone or not email:
                st.error("All fields are required.")
                return

            st.session_state["visitor_info"].update({
                "name": name,
                "phone": phone,
                "email": email,
            })
            st.session_state["visitor_step"] = "secondary"
            st.rerun()


# ==============================================================================
# 6. SECONDARY DETAILS FORM
# ==============================================================================

def render_secondary_details():

    st.markdown("### Visit Information")

    with st.form("secondary_form"):

        visit_type = st.selectbox(
            "Visit Type *",
            ["Business", "Interview", "Meeting", "Personal"],
            index=0
        )

        purpose = st.text_input("Purpose of Visit *")
        person_to_meet = st.text_input("Person to Meet *")
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])

        submitted = st.form_submit_button("Continue →")

        if submitted:
            if not purpose or not person_to_meet:
                st.error("Purpose & Person to Meet are mandatory.")
                return

            st.session_state["visitor_info"].update({
                "visit_type": visit_type,
                "purpose": purpose,
                "person_to_meet": person_to_meet,
                "gender": gender
            })

            # Save to DB (optional depending on your design)
            save_visitor_to_db(st.session_state["visitor_info"])

            # Navigate to visitor_identity page
            st.session_state["current_page"] = "visitor_identity"
            st.rerun()


# ==============================================================================
# 7. MAIN RENDER FUNCTION
# ==============================================================================

def render_visitor_registration():

    initialize_state()
    apply_styles()

    # Auth enforcement
    if not st.session_state.get("admin_logged_in"):
        st.error("Please login to continue.")
        st.stop()

    if not st.session_state.get("company_id"):
        st.error("Company ID Missing. Re-login required.")
        st.stop()

    render_header()

    if st.session_state["visitor_step"] == "primary":
        render_primary_details()
    elif st.session_state["visitor_step"] == "secondary":
        render_secondary_details()


# ==============================================================================
# DEBUG MODE
# ==============================================================================

if __name__ == "__main__":
    st.session_state["admin_logged_in"] = True
    st.session_state["company_id"] = 1

    render_visitor_registration()
