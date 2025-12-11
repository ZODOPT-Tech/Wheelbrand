import streamlit as st
from datetime import datetime
import mysql.connector
import boto3
import json
from mysql.connector import Error
from botocore.exceptions import ClientError

# ===========================================================
# AWS + DB
# ===========================================================
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
DEFAULT_DB_PORT = 3306


@st.cache_resource(ttl=3600)
def get_db_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    resp = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(resp["SecretString"])


@st.cache_resource
def get_fast_connection():
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


# ===========================================================
# CSS + HEADER
# ===========================================================
def load_styles():
    st.markdown("""
        <style>
        .header-box {
            background: linear-gradient(90deg, #5036FF, #9C2CFF);
            padding: 26px;
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
        .tab-row {
            display: flex;
            gap: 40px;
            padding-left: 5px;
            margin-top: 10px;
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
        .stTextInput > div > div > input {
            background: #F3F5FB !important;
            border-radius: 8px !important;
            border: 1px solid #DDE2EE !important;
            padding: 10px 14px !important;
        }
        .primary-btn button {
            background: linear-gradient(90deg, #5036FF, #9C2CFF) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 11px !important;
            font-size: 17px !important;
            font-weight: 600 !important;
        }
        </style>
    """, unsafe_allow_html=True)


def render_header(step="primary"):
    load_styles()
    st.markdown("""
        <div class="header-box">
            Visitor Registration
            <div class="header-sub">Please fill in your details</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="tab-row">
            <div class="tab-item {'tab-active' if step == 'primary' else ''}">PRIMARY DETAILS</div>
            <div class="tab-item {'tab-active' if step == 'secondary' else ''}">SECONDARY DETAILS</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===========================================================
# PRIMARY FORM
# ===========================================================
def render_primary_form():
    render_header("primary")

    if "visitor_data" not in st.session_state:
        st.session_state["visitor_data"] = {}

    d = st.session_state["visitor_data"]

    name = st.text_input("Name *", d.get("name", ""))
    phone = st.text_input("Phone *", d.get("phone", ""))
    email = st.text_input("Email *", d.get("email", ""))

    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)

    if st.button("Next →", use_container_width=True):
        if not name or not phone or not email:
            st.error("All fields are required.")
            return

        st.session_state["visitor_data"].update(
            {"name": name, "phone": phone, "email": email}
        )

        st.session_state["current_page"] = "visitor_secondarydetails"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
