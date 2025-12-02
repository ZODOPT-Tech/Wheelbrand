import streamlit as st
from datetime import datetime
import json
import mysql.connector
from mysql.connector import Error
import boto3
from botocore.exceptions import ClientError


# ============================== AWS + DB ==============================
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
DEFAULT_DB_PORT = 3306


@st.cache_resource(ttl=3600)
def get_db_credentials():
    try:
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        secret_data = json.loads(resp["SecretString"])

        return {
            "DB_HOST": secret_data["DB_HOST"],
            "DB_NAME": secret_data["DB_NAME"],
            "DB_USER": secret_data["DB_USER"],
            "DB_PASSWORD": secret_data["DB_PASSWORD"],
        }

    except Exception as e:
        st.error(f"Error fetching credentials: {e}")
        st.stop()


@st.cache_resource
def get_fast_connection():
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
        st.error(f"Database connection failed: {e}")
        st.stop()


def save_visitor_data_to_db(data):
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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s)
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


# ============================== UI CSS ==============================
def inject_ui_styles():
    st.markdown("""
        <style>
            .header-box {
                background: linear-gradient(90deg, #4e48f1, #8b32ff);
                padding: 25px;
                color: white;
                font-size: 28px;
                font-weight: 700;
                border-radius: 12px;
                margin-bottom: 25px;
            }
            .header-sub {
                font-size: 15px;
                opacity: 0.9;
                margin-top: -5px;
            }
            .tab-row {
                display: flex;
                margin-bottom: 10px;
                margin-top: 20px;
            }
            .tab-item {
                padding: 12px 25px;
                cursor: pointer;
                font-weight: 600;
                border-bottom: 3px solid transparent;
                color: #666;
                font-size: 16px;
            }
            .tab-active {
                color: #4e48f1;
                border-bottom: 3px solid #4e48f1;
            }
            .container-box {
                background: #ffffff;
                padding: 30px;
                border-radius: 14px;
                box-shadow: 0px 4px 18px rgba(0,0,0,0.06);
                margin-top: 15px;
            }
            label {
                font-weight: 600 !important;
            }
        </style>
    """, unsafe_allow_html=True)


# ============================== HEADER ==============================
def render_header():
    inject_ui_styles()
    st.markdown("""
        <div class="header-box">
            Visitor Registration
            <div class="header-sub">Please fill in your details</div>
        </div>
    """, unsafe_allow_html=True)

    step = st.session_state["registration_step"]
    st.markdown(f"""
        <div class="tab-row">
            <div class="tab-item {'tab-active' if step=='primary' else ''}">PRIMARY DETAILS</div>
            <div class="tab-item {'tab-active' if step=='secondary' else ''}">SECONDARY DETAILS</div>
        </div>
    """, unsafe_allow_html=True)


# ============================== PRIMARY FORM ==============================
def render_primary_form():

    data = st.session_state["visitor_data"]

    st.markdown('<div class="container-box">', unsafe_allow_html=True)

    name = st.text_input("Name *", data.get("name", ""), placeholder="Enter your full name")
    phone = st.text_input("Phone *", data.get("phone", ""), placeholder="81234 56789")
    email = st.text_input("Email *", data.get("email", ""), placeholder="mail@example.com")

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

    st.markdown('</div>', unsafe_allow_html=True)


# ============================== SECONDARY FORM ==============================
def render_secondary_form():

    d = st.session_state["visitor_data"]
    st.markdown('<div class="container-box">', unsafe_allow_html=True)

    visit_type = st.text_input("Visit Type", d.get("visit_type", ""))
    from_company = st.text_input("From Company", d.get("from_company", ""))
    department = st.text_input("Department", d.get("department", ""))
    designation = st.text_input("Designation", d.get("designation", ""))

    address_line_1 = st.text_input("Address Line 1", d.get("address_line_1", ""))

    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input("City", d.get("city", ""))
    with col2:
        state = st.text_input("State", d.get("state", ""))

    col3, col4 = st.columns(2)
    with col3:
        postal_code = st.text_input("Postal Code", d.get("postal_code", ""))
    with col4:
        country = st.text_input("Country", d.get("country", ""))

    gender = st.radio("Gender", ["Male", "Female", "Others"], horizontal=True)

    purpose = st.text_input("Purpose of Visit", d.get("purpose", ""))
    person_to_meet = st.text_input("Person to Meet *", d.get("person_to_meet", ""))

    st.markdown("#### Belongings")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        bags = st.checkbox("Bags", d.get("has_bags", False))
        electronics = st.checkbox("Electronic Items", d.get("has_electronic_items", False))
        charger = st.checkbox("Charger", d.get("has_charger", False))

    with col_b2:
        documents = st.checkbox("Documents", d.get("has_documents", False))
        laptop = st.checkbox("Laptop", d.get("has_laptop", False))
        power_bank = st.checkbox("Power Bank", d.get("has_power_bank", False))

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
            "has_documents": documents,
            "has_electronic_items": electronics,
            "has_laptop": laptop,
            "has_charger": charger,
            "has_power_bank": power_bank
        })

        st.session_state["current_page"] = "visitor_identity"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ============================== ENTRY FOR main.py ==============================
def render_details_page():

    # Must be logged in
    if not st.session_state.get("admin_logged_in"):
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
