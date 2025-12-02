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
        return json.loads(resp["SecretString"])
    except Exception as e:
        st.error(f"Error fetching DB credentials: {e}")
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
            connection_timeout=10,
        )
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        st.stop()


# ============================== CSS ==============================
def load_styles():
    st.markdown(
        """
        <style>

        /* Gradient Header */
        .header-box {
            background: linear-gradient(90deg, #5036FF, #9C2CFF);
            padding: 26px 26px 18px 26px;
            border-radius: 14px;
            color: white;
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .header-sub {
            font-size: 15px;
            opacity: 0.92;
            margin-top: -6px;
        }

        /* Tabs */
        .tab-row {
            display: flex;
            gap: 40px;
            padding: 10px 5px 0px 5px;
            margin-top: 8px;
        }
        .tab-item {
            font-size: 17px;
            font-weight: 600;
            padding-bottom: 6px;
            cursor: pointer;
            color: #777;
        }
        .tab-active {
            color: #4F49FF;
            border-bottom: 3px solid #4F49FF;
        }

        /* White form container */
        .form-container {
            background: white;
            padding: 30px 30px 22px 30px;
            border-radius: 14px;
            margin-top: 18px;
            box-shadow: 0px 4px 18px rgba(0,0,0,0.06);
        }

        label {
            font-weight: 600 !important;
            margin-top: 10px !important;
        }

        /* Input styling */
        .stTextInput > div > div > input {
            background: #F3F5FB !important;
            border-radius: 8px !important;
            border: 1px solid #DDE2EE !important;
            padding: 10px 14px !important;
        }

        /* Gradient Button */
        .primary-btn button {
            background: linear-gradient(90deg, #5036FF, #9C2CFF) !important;
            border: none !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 11px !important;
            font-size: 17px !important;
            font-weight: 600 !important;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================== HEADER ==============================
def render_header():

    load_styles()

    st.markdown(
        """
        <div class="header-box">
            Visitor Registration
            <div class="header-sub">Please fill in your details</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    step = st.session_state["registration_step"]

    st.markdown(
        f"""
        <div class="tab-row">
            <div class="tab-item {'tab-active' if step=='primary' else ''}">PRIMARY DETAILS</div>
            <div class="tab-item {'tab-active' if step=='secondary' else ''}">SECONDARY DETAILS</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================== PRIMARY FORM ==============================
def render_primary_form():

    d = st.session_state["visitor_data"]

    st.markdown('<div class="form-container">', unsafe_allow_html=True)

    name = st.text_input("Name *", d.get("name", ""), placeholder="Enter your full name")
    phone = st.text_input("Phone *", d.get("phone", ""), placeholder="81234 56789")
    email = st.text_input("Email *", d.get("email", ""), placeholder="mail@example.com")

    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
    if st.button("Next →", use_container_width=True):
        if not name or not phone or not email:
            st.error("All fields are required.")
            return

        st.session_state["visitor_data"].update(
            {"name": name, "phone": phone, "email": email}
        )

        st.session_state["registration_step"] = "secondary"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ============================== SECONDARY FORM ==============================
def render_secondary_form():

    d = st.session_state["visitor_data"]

    st.markdown('<div class="form-container">', unsafe_allow_html=True)

    visit_type = st.text_input("Visit Type", d.get("visit_type", ""))
    from_company = st.text_input("From Company", d.get("from_company", ""))
    department = st.text_input("Department", d.get("department", ""))
    designation = st.text_input("Designation", d.get("designation", ""))
    address_line_1 = st.text_input("Address Line 1", d.get("address_line_1", ""))

    col1, col2 = st.columns(2)
    city = col1.text_input("City", d.get("city", ""))
    state = col2.text_input("State", d.get("state", ""))

    col3, col4 = st.columns(2)
    postal_code = col3.text_input("Postal Code", d.get("postal_code", ""))
    country = col4.text_input("Country", d.get("country", ""))

    gender = st.radio("Gender", ["Male", "Female", "Others"], horizontal=True)

    purpose = st.text_input("Purpose of Visit", d.get("purpose", ""))
    person_to_meet = st.text_input("Person to Meet *", d.get("person_to_meet", ""))

    st.markdown("### Belongings")

    colb1, colb2 = st.columns(2)
    with colb1:
        bags = st.checkbox("Bags", d.get("has_bags", False))
        electronics = st.checkbox("Electronic Items", d.get("has_electronic_items", False))
        charger = st.checkbox("Charger", d.get("has_charger", False))
    with colb2:
        documents = st.checkbox("Documents", d.get("has_documents", False))
        laptop = st.checkbox("Laptop", d.get("has_laptop", False))
        power_bank = st.checkbox("Power Bank", d.get("has_power_bank", False))

    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
    if st.button("Continue → Identity Capture", use_container_width=True):

        if not person_to_meet:
            st.error("Person to Meet is required.")
            return

        st.session_state["visitor_data"].update(
            {
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
                "has_power_bank": power_bank,
            }
        )

        st.session_state["current_page"] = "visitor_identity"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ============================== ENTRY FOR main.py ==============================
def render_details_page():

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
