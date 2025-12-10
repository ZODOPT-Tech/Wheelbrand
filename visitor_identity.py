import streamlit as st
import mysql.connector
import boto3
import json
from datetime import datetime
import base64

# =============================
# AWS Config
# =============================
AWS_REGION = "ap-south-1"
AWS_BUCKET = "zodoptvisiorsmanagement"
AWS_SECRET_ARN = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
FOLDER_NAME = "visitor_photos"


# =============================
# Secrets
# =============================
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


# =============================
# DB Fetch
# =============================
def get_visitor_data(visitor_id: int):
    conn = get_db_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT 
            visitor_id,
            full_name,
            from_company,
            person_to_meet,
            visit_type,
            registration_timestamp
        FROM visitors
        WHERE visitor_id = %s;
    """, (visitor_id,))

    data = cur.fetchone()
    cur.close()
    return data


# =============================
# Save URL to DB
# =============================
def save_photo_url(visitor_id, photo_url):
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO visitor_identity (visitor_id, photo_url)
        VALUES (%s, %s)
    """, (visitor_id, photo_url))

    cur.close()


# =============================
# S3 Upload
# =============================
def upload_photo(visitor, photo_bytes):
    s3 = boto3.client("s3")

    # Sanitise
    company = visitor["from_company"].replace(" ", "_")
    name = visitor["full_name"].replace(" ", "_")
    timestamp = int(datetime.now().timestamp())

    key = f"{FOLDER_NAME}/{company}/{name}_{timestamp}.jpg"

    s3.put_object(
        Bucket=AWS_BUCKET,
        Key=key,
        Body=photo_bytes,
        ContentType="image/jpeg"
    )

    url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
    return url


# =============================
# Digital Visitor Pass
# =============================
def show_pass(visitor, photo_bytes, photo_url):
    b64 = base64.b64encode(photo_bytes).decode()

    st.markdown(f"""
        <div style="width:420px;
                    background:white;
                    box-shadow:0 4px 12px rgba(0,0,0,0.14);
                    border-radius:12px;
                    padding:20px;
                    margin-top:20px;">
            <h2 style="text-align:center;color:#5036FF;">VISITOR PASS</h2>

            <div style="text-align:center;margin-bottom:10px;">
                <img src="data:image/jpeg;base64,{b64}"
                     style="width:140px;height:140px;
                            border-radius:10px;
                            border:2px solid #5036FF;">
            </div>

            <p><b>Name:</b> {visitor['full_name']}</p>
            <p><b>From:</b> {visitor['from_company']}</p>
            <p><b>To Meet:</b> {visitor['person_to_meet']}</p>
            <p><b>Visitor ID:</b> #{visitor['visitor_id']}</p>
            <p><b>Date:</b> {datetime.now().strftime("%d-%m-%Y %H:%M")}</p>

            <p><b>Photo URL:</b><br>{photo_url}</p>
        </div>
    """, unsafe_allow_html=True)


# =============================
# MAIN Page
# =============================
def render_identity_page():

    # AUTH & SESSION CHECKS
    if not st.session_state.get("admin_logged_in", False):
        st.warning("Unauthorized")
        st.session_state["current_page"] = "visitor_login"
        st.rerun()

    if "current_visitor_id" not in st.session_state:
        st.error("No visitor selected")
        st.session_state["current_page"] = "visitor_details"
        st.rerun()

    visitor_id = st.session_state["current_visitor_id"]
    visitor = get_visitor_data(visitor_id)

    # HEADER
    st.markdown("""
        <h2 style='color:#5036FF;
                  font-weight:700;
                  margin-bottom:10px;'>🆔 Identity Capture</h2>
    """, unsafe_allow_html=True)

    st.write(f"**Name:** {visitor['full_name']}")
    st.write(f"**Company:** {visitor['from_company']}")
    st.write(f"**Meeting:** {visitor['person_to_meet']}")

    photo = st.camera_input("Capture Photo")

    # ACTION
    if st.button("Save & Generate Pass"):
        if not photo:
            st.error("Please capture the photo")
            return

        photo_bytes = photo.getvalue()

        with st.spinner("Uploading photo..."):
            photo_url = upload_photo(visitor, photo_bytes)
            save_photo_url(visitor_id, photo_url)

        st.success("Visitor profile saved successfully!")
        show_pass(visitor, photo_bytes, photo_url)

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("New Visitor"):
                st.session_state.pop("current_visitor_id", None)
                st.session_state["current_page"] = "visitor_details"
                st.rerun()

        with c2:
            if st.button("Dashboard"):
                st.session_state["current_page"] = "visitor_dashboard"
                st.rerun()

        with c3:
            if st.button("Logout"):
                st.session_state.clear()
                st.session_state["current_page"] = "visitor_login"
                st.rerun()

    if st.button("← Back"):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()
