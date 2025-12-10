import streamlit as st
import mysql.connector
import boto3
import json
import base64
from datetime import datetime


# =========================================================
# AWS & DB CONFIG
# =========================================================
AWS_REGION = "ap-south-1"
AWS_BUCKET = "zodoptvisiorsmanagement"
FOLDER_NAME = "visitor_photos"
AWS_SECRET_ARN = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"


# =========================================================
# DB CREDENTIALS
# =========================================================
@st.cache_resource
def get_db_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    sec = client.get_secret_value(SecretId=AWS_SECRET_ARN)
    return json.loads(sec["SecretString"])


@st.cache_resource
def get_db_conn():
    c = get_db_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True,
    )


# =========================================================
# GET VISITOR DETAILS
# =========================================================
def get_visitor(visitor_id: int):
    conn = get_db_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT visitor_id, full_name, from_company, person_to_meet
        FROM visitors WHERE visitor_id = %s;
    """, (visitor_id,))
    d = cur.fetchone()
    cur.close()
    return d


# =========================================================
# SAVE PHOTO URL
# =========================================================
def save_photo_url(visitor_id, photo_url):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO visitor_identity (visitor_id, photo_url)
        VALUES (%s, %s)
    """, (visitor_id, photo_url))
    cur.close()


# =========================================================
# UPLOAD TO S3
# =========================================================
def upload_photo(visitor, bytes_data):
    s3 = boto3.client("s3")

    company = visitor["from_company"].replace(" ", "_")
    name = visitor["full_name"].replace(" ", "_")
    ts = int(datetime.now().timestamp())

    key = f"{FOLDER_NAME}/{company}/{name}_{ts}.jpg"

    s3.put_object(
        Bucket=AWS_BUCKET,
        Key=key,
        Body=bytes_data,
        ContentType="image/jpeg"
    )

    return f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"


# =========================================================
# SHOW PASS UI
# =========================================================
def show_pass(visitor, photo_bytes, photo_url):

    b64 = base64.b64encode(photo_bytes).decode()

    st.markdown("""
        <h2 style='text-align:center;
                   color:#4a3aff;
                   font-weight:800;
                   font-size:38px;
                   margin-bottom:5px'>
            VISITOR PASS
        </h2>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style="
            width:450px;
            margin:20px auto;
            border-radius:16px;
            background:white;
            padding:22px;
            box-shadow:0px 6px 18px rgba(0,0,0,0.10);
        ">
            <div style='text-align:center;margin-bottom:14px'>
                <img src="data:image/jpeg;base64,{b64}"
                     style="width:150px;height:150px;
                            border-radius:10px;
                            border:2px solid #4a3aff;">
            </div>

            <p><b>Name:</b> {visitor['full_name']}</p>
            <p><b>From:</b> {visitor['from_company']}</p>
            <p><b>To Meet:</b> {visitor['person_to_meet']}</p>
            <p><b>Visitor ID:</b> #{visitor['visitor_id']}</p>
            <p><b>Date:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}</p>

            <p><b>Photo URL:</b><br>{photo_url}</p>
        </div>
    """, unsafe_allow_html=True)


    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("New Visitor"):
            st.session_state.pop("current_visitor_id", None)
            st.session_state.pop("visitor_pass", None)
            st.session_state["current_page"] = "visitor_details"
            st.rerun()

    with col2:
        if st.button("Dashboard"):
            st.session_state.pop("visitor_pass", None)
            st.session_state["current_page"] = "visitor_dashboard"
            st.rerun()

    with col3:
        if st.button("Logout"):
            st.session_state.clear()
            st.session_state["current_page"] = "visitor_login"
            st.rerun()


# =========================================================
# MAIN SINGLE PAGE
# =========================================================
def render_identity_page():

    # Redirect if no login
    if not st.session_state.get("admin_logged_in", False):
        st.session_state["current_page"] = "visitor_login"
        st.rerun()

    # Redirect if call without visitor
    if "current_visitor_id" not in st.session_state:
        st.session_state["current_page"] = "visitor_details"
        st.rerun()

    # If pass already created → Show pass
    if "visitor_pass" in st.session_state:
        data = st.session_state["visitor_pass"]
        show_pass(data["visitor"], data["photo_bytes"], data["photo_url"])
        return

    visitor = get_visitor(st.session_state["current_visitor_id"])

    # HEADER
    st.markdown("""
        <h2 style='color:#4a3aff;
                   text-align:center;
                   font-weight:800;
                   margin-bottom:6px'>
            Capture Visitor Photo
        </h2>
        <p style='text-align:center;color:#777;margin-top:-6px'>
            This will be used to generate the digital visitor pass
        </p>
        <hr style='margin-bottom:22px'>
    """, unsafe_allow_html=True)

    st.write(f"**Name:** {visitor['full_name']}")
    st.write(f"**Company:** {visitor['from_company']}")
    st.write(f"**Meeting:** {visitor['person_to_meet']}")

    # Small camera size
    photo = st.camera_input("Take Photo", label_visibility="collapsed")

    if st.button("Save & Generate Pass", type="primary"):
        if not photo:
            st.error("Please capture photo")
            return

        bytes_data = photo.getvalue()

        with st.spinner("Creating pass..."):
            # Upload and save
            photo_url = upload_photo(visitor, bytes_data)
            save_photo_url(visitor["visitor_id"], photo_url)

        # Store pass in memory
        st.session_state["visitor_pass"] = {
            "visitor": visitor,
            "photo_bytes": bytes_data,
            "photo_url": photo_url,
        }

        st.rerun()

    if st.button("← Back"):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()


# =========================================================
# LOCAL TESTING
# =========================================================
if __name__ == "__main__":
    st.session_state["admin_logged_in"] = True
    st.session_state["current_visitor_id"] = 1
    render_identity_page()
