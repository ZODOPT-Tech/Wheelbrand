import streamlit as st
from datetime import datetime
import json
import mysql.connector
from mysql.connector import Error
import boto3
from botocore.exceptions import ClientError


# ========================== AWS + DB CREDENTIALS =============================
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
DEFAULT_DB_PORT = 3306


@st.cache_resource(ttl=3600)
def get_db_credentials():
    """Retrieve DB credentials from AWS Secrets Manager."""
    try:
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)

        if "SecretString" not in resp:
            raise ValueError("SecretString missing from AWS Secret.")

        secret_data = json.loads(resp["SecretString"])
        return {
            "DB_HOST": secret_data["DB_HOST"],
            "DB_NAME": secret_data["DB_NAME"],
            "DB_USER": secret_data["DB_USER"],
            "DB_PASSWORD": secret_data["DB_PASSWORD"],
        }

    except Exception as e:
        st.error(f"Error retrieving DB Credentials: {e}")
        st.stop()


@st.cache_resource
def get_fast_connection():
    """Create & reuse MySQL connection."""
    try:
        creds = get_db_credentials()
        conn = mysql.connector.connect(
            host=creds["DB_HOST"],
            user=creds["DB_USER"],
            password=creds["DB_PASSWORD"],
            database=creds["DB_NAME"],
            port=DEFAULT_DB_PORT,
            autocommit=True,
            connection_timeout=10,
        )
        return conn

    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        st.stop()


# ========================== SAVE VISITOR DATA ================================
def save_visitor_data_to_db(data):
    """Insert collected visitor details into DB."""
    conn = get_fast_connection()
    cursor = None

    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO visitors 
            (company_id, registration_timestamp, full_name, phone_number, email, 
             visit_type, from_company, department, designation, address_line_1, 
             city, state, postal_code, country, gender, purpose, person_to_meet,
             has_bags, has_documents, has_electronic_items, has_laptop, has_charger, has_power_bank)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            st.session_state["company_id"],
            datetime.now(),
            data["name"],
            data["phone"],
            data["email"],
            data.get("visit_type"),
            data.get("from_company"),
            data.get("department"),
            data.get("designation"),
            data.get("address_line_1"),
            data.get("city"),
            data.get("state"),
            data.get("postal_code"),
            data.get("country"),
            data.get("gender"),
            data.get("purpose"),
            data.get("person_to_meet"),
            data.get("has_bags"),
            data.get("has_documents"),
            data.get("has_electronic_items"),
            data.get("has_laptop"),
            data.get("has_charger"),
            data.get("has_power_bank"),
        )

        cursor.execute(query, values)
        conn.commit()
        return True

    except Exception as e:
        st.error(f"Database Save Error: {e}")
        return False

    finally:
        if cursor:
            cursor.close()


# ========================== CUSTOM HEADER UI ================================
def render_header():
    st.markdown(
        """
        <div style="
            background:#5d28a5;
            color:white;
            padding:15px 25px;
            font-size:24px;
            border-radius:8px;
            margin-bottom:20px;
            font-weight:700;">
            VISITOR REGISTRATION
        </div>
        """,
        unsafe_allow_html=True,
    )


# ========================== PRIMARY FORM ================================
def render_primary_form():
    st.subheader("Primary Contact Information")

    name = st.text_input("Full Name *", st.session_state["visitor_data"].get("name", ""))
    phone = st.text_input("Phone Number *", st.session_state["visitor_data"].get("phone", ""))
    email = st.text_input("Email Address *", st.session_state["visitor_data"].get("email", ""))

    if st.button("Next →", use_container_width=True):
        if not name or not phone or not email:
            st.error("Please fill all required fields.")
            return

        st.session_state["visitor_data"].update({
            "name": name,
            "phone": phone,
            "email": email
        })

        st.session_state["registration_step"] = "secondary"
        st.rerun()


# ========================== SECONDARY FORM ================================
def render_secondary_form():
    st.subheader("Visit Details & Additional Information")

    d = st.session_state["visitor_data"]

    visit_type = st.text_input("Visit Type", d.get("visit_type", ""))
    from_company = st.text_input("From Company", d.get("from_company", ""))
    department = st.text_input("Department", d.get("department", ""))
    designation = st.text_input("Designation", d.get("designation", ""))

    address_line_1 = st.text_input("Address Line 1", d.get("address_line_1", ""))
    city = st.text_input("City", d.get("city", ""))
    state = st.text_input("State", d.get("state", ""))
    postal_code = st.text_input("Postal Code", d.get("postal_code", ""))
    country = st.text_input("Country", d.get("country", ""))

    gender = st.radio("Gender", ["Male", "Female", "Others"], index=0)

    purpose = st.text_input("Purpose of Visit", d.get("purpose", ""))
    person_to_meet = st.text_input("Person to Meet *", d.get("person_to_meet", ""))

    bags = st.checkbox("Bags", d.get("has_bags", False))
    docs = st.checkbox("Documents", d.get("has_documents", False))
    electronics = st.checkbox("Electronic Items", d.get("has_electronic_items", False))
    laptop = st.checkbox("Laptop", d.get("has_laptop", False))
    charger = st.checkbox("Charger", d.get("has_charger", False))
    power_bank = st.checkbox("Power Bank", d.get("has_power_bank", False))

    if st.button("Continue → Identity Verification", use_container_width=True):
        if not person_to_meet:
            st.error("'Person to Meet' is required.")
            return

        st.session_state["visitor_data"].update({
            "visit_type": visit_type,
            "from_company": from_company,
            "department": department,
            "designation": designation,
            "address_line_1": address_line_1,
            "city": city,
            "state": state,
            "postal_code": postal_code,
            "country": country,
            "gender": gender,
            "purpose": purpose,
            "person_to_meet": person_to_meet,
            "has_bags": bags,
            "has_documents": docs,
            "has_electronic_items": electronics,
            "has_laptop": laptop,
            "has_charger": charger,
            "has_power_bank": power_bank,
        })

        # ---- Navigate to visitor_identity page ----
        st.session_state["current_page"] = "visitor_identity"
        st.rerun()


# ========================== MAIN RENDER FUNCTION (Used by main.py) ====================
def render_details_page():
    """Page entry point"""

    # Enforce admin login
    if not st.session_state.get("admin_logged_in"):
        st.error("Please log in as Admin to continue.")
        st.session_state["current_page"] = "visitor_login"
        st.rerun()

    if "visitor_data" not in st.session_state:
        st.session_state["visitor_data"] = {}

    if "registration_step" not in st.session_state:
        st.session_state["registration_step"] = "primary"

    render_header()

    if st.session_state["registration_step"] == "primary":
        render_primary_form()

    else:
        render_secondary_form()

