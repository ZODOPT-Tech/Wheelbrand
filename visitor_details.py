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

        data = json.loads(resp["SecretString"])
        return data

    except Exception as e:
        st.error(f"Error retrieving DB Credentials: {e}")
        st.stop()


@st.cache_resource
def get_fast_connection():
    """Create & reuse MySQL connection."""
    creds = get_db_credentials()
    try:
        conn = mysql.connector.connect(
            host=creds["DB_HOST"],
            user=creds["DB_USER"],
            password=creds["DB_PASSWORD"],
            database=creds["DB_NAME"],
            port=DEFAULT_DB_PORT,
            autocommit=True
        )
        return conn
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        st.stop()


# ========================== SAVE VISITOR DATA ================================
def save_visitor_data_to_db(data):
    conn = get_fast_connection()
    cursor = None

    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO visitors 
            (company_id, registration_timestamp, full_name, phone_number, email,
             visit_type, from_company, department, designation, address_line_1,
             city, state, postal_code, country, gender, purpose, person_to_meet,
             has_bags, has_documents, has_electronic_items, has_laptop, has_charger, has_power_bank)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            st.session_state["company_id"],
            datetime.now(),
            data["name"], data["phone"], data["email"],
            data.get("visit_type"), data.get("from_company"),
            data.get("department"), data.get("designation"),
            data.get("address_line_1"), data.get("city"),
            data.get("state"), data.get("postal_code"), data.get("country"),
            data.get("gender"), data.get("purpose"), data.get("person_to_meet"),
            data.get("has_bags"), data.get("has_documents"),
            data.get("has_electronic_items"), data.get("has_laptop"),
            data.get("has_charger"), data.get("has_power_bank"),
        )

        cursor.execute(sql, values)
        conn.commit()
        return True

    except Exception as e:
        st.error(f"DB Save Error: {e}")
        return False

    finally:
        if cursor:
            cursor.close()


# ========================== BEAUTIFUL UI CSS ================================
def inject_ui_styles():
    st.markdown("""
        <style>

        body {
            font-family: 'Inter', sans-serif;
        }

        /* Gradient Header */
        .header-box {
            background: linear-gradient(90deg, #4a32ea, #9935ff);
            padding: 30px;
            border-radius: 12px;
            color: white;
            margin-bottom: 0px;
        }

        .header-title {
            font-size: 30px;
            font-weight: 700;
        }
        
        .header-subtitle {
            font-size: 15px;
            opacity: 0.95;
            margin-top: -5px;
        }

        /* Tab Navigation */
        .tabs-box {
            background: #ffffff;
            padding: 10px 0 0 0;
            border-radius: 0 0 10px 10px;
        }

        .tab-item {
            display: inline-block;
            padding: 12px 32px;
            margin-right: 10px;
            font-size: 17px;
            font-weight: 600;
            color: #555;
            cursor: pointer;
            border-bottom: 3px solid transparent;
        }

        .tab-active {
            color: #4a32ea !important;
            border-bottom: 3px solid #4a32ea !important;
        }

        /* Input boxes */
        .stTextInput input, .stTextArea textarea {
            background: #f7f9fc !important;
            border-radius: 10px !important;
            padding: 12px !important;
            border: 1px solid #e2e6ef !important;
        }

        </style>
    """, unsafe_allow_html=True)


# ========================== UI HEADER ================================
def render_header():
    inject_ui_styles()
    st.markdown("""
        <div class="header-box">
            <div class="header-title">Visitor Registration</div>
            <div class="header-subtitle">Please fill in your details</div>
        </div>
    """, unsafe_allow_html=True)

    step = st.session_state["registration_step"]
    st.markdown("""
        <div class="tabs-box">
            <span class="tab-item {p_active}">PRIMARY DETAILS</span>
            <span class="tab-item {s_active}">SECONDARY DETAILS</span>
        </div>
    """.format(
        p_active="tab-active" if step == "primary" else "",
        s_active="tab-active" if step == "secondary" else ""
    ), unsafe_allow_html=True)


# ========================== PRIMARY FORM ================================
def render_primary_form():

    data = st.session_state["visitor_data"]

    name = st.text_input("Name *", data.get("name", ""), placeholder="Enter your full name")
    phone = st.text_input("Phone *", data.get("phone", ""), placeholder="81234 56789")
    email = st.text_input("Email *", data.get("email", ""), placeholder="mail@example.com")

    st.write("")
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

    data = st.session_state["visitor_data"]

    visit_type = st.text_input("Visit Type", data.get("visit_type", ""))
    from_company = st.text_input("From Company", data.get("from_company", ""))
    department = st.text_input("Department", data.get("department", ""))
    designation = st.text_input("Designation", data.get("designation", ""))

    address_line_1 = st.text_input("Address Line 1", data.get("address_line_1", ""))
    city = st.text_input("City", data.get("city", ""))
    state = st.text_input("State", data.get("state", ""))
    postal_code = st.text_input("Postal Code", data.get("postal_code", ""))
    country = st.text_input("Country", data.get("country", ""))

    gender = st.radio("Gender", ["Male", "Female", "Others"], horizontal=True)

    purpose = st.text_input("Purpose of Visit", data.get("purpose", ""))
    person_to_meet = st.text_input("Person to Meet *", data.get("person_to_meet", ""))

    bags = st.checkbox("Bags", data.get("has_bags", False))
    docs = st.checkbox("Documents", data.get("has_documents", False))
    electronics = st.checkbox("Electronic Items", data.get("has_electronic_items", False))
    laptop = st.checkbox("Laptop", data.get("has_laptop", False))
    charger = st.checkbox("Charger", data.get("has_charger", False))
    power_bank = st.checkbox("Power Bank", data.get("has_power_bank", False))

    st.write("")
    if st.button("Continue → Identity Verification", use_container_width=True):

        if not person_to_meet:
            st.error("Person to Meet is required.")
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
            "has_power_bank": power_bank
        })

        st.session_state["current_page"] = "visitor_identity"
        st.rerun()


# ========================== MAIN ENTRY FUNCTION ================================
def render_details_page():

    if not st.session_state.get("admin_logged_in"):
        st.error("Access Denied. Please log in.")
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
