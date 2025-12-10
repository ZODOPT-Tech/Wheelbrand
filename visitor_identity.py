import streamlit as st
import mysql.connector
import boto3
import json
from datetime import datetime
import base64
import io
from PIL import Image as PILImage


AWS_REGION = "ap-south-1"
AWS_BUCKET = "zodoptvisiorsmanagement"
AWS_SECRET_ARN = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"


# ============ Credentials ============
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
        autocommit=True
    )


# ============ Visitor Fetch ============
def get_visitor(visitor_id):
    conn = get_db_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT visitor_id, full_name, from_company, person_to_meet
        FROM visitors
        WHERE visitor_id=%s
    """, (visitor_id,))
    data = cur.fetchone()
    cur.close()
    return data


# ============ DB Update ============

def mark_pass_generated(visitor_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE visitors SET pass_generated=1 WHERE visitor_id=%s",
        (visitor_id,)
    )
    cur.close()


def insert_identity_record(visitor_id, photo_url):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO visitor_identity (visitor_id, photo_url)
        VALUES (%s, %s)
    """, (visitor_id, photo_url))
    cur.close()


# ============ S3 Upload ============
def upload_photo(visitor, photo_bytes):
    company = visitor["from_company"].strip().replace(" ", "_").lower()
    name = visitor["full_name"].strip().replace(" ", "_").lower()
    ts = int(datetime.now().timestamp())

    filename = f"visitor_photos/{company}/{name}_{ts}.jpg"

    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=AWS_BUCKET,
        Key=filename,
        Body=photo_bytes,
        ContentType="image/jpeg"
    )

    return f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"


# ============ Visitor Pass UI ============
def render_pass(visitor, photo_bytes):
    b64 = base64.b64encode(photo_bytes).decode()

    st.markdown(f"""
        <div style="
            width:350px;
            background:white;
            border-radius:14px;
            padding:18px;
            box-shadow:0 4px 16px rgba(0,0,0,0.18);
        ">
            <h2 style="text-align:center;color:#5036FF;margin-bottom:12px;">
                Visitor Pass
            </h2>

            <div style="text-align:center;margin-bottom:14px;">
                <img src="data:image/jpeg;base64,{b64}"
                     style="width:120px;height:120px;
                            border-radius:8px;border:2px solid #5036FF;">
            </div>

            <p><strong>Name:</strong> {visitor['full_name']}</p>
            <p><strong>From:</strong> {visitor['from_company']}</p>
            <p><strong>To Meet:</strong> {visitor['person_to_meet']}</p>
            <p><strong>Visitor ID:</strong> #{visitor['visitor_id']}</p>
            <p><strong>Date:</strong> {datetime.now().strftime("%d-%m-%Y %H:%M")}</p>
        </div>
    """, unsafe_allow_html=True)


# ============ Page Renderer ============
def render_identity_page():
    if not st.session_state.get("admin_logged_in", False):
        st.session_state["current_page"] = "visitor_login"
        st.rerun()

    if "current_visitor_id" not in st.session_state:
        st.session_state["current_page"] = "visitor_details"
        st.rerun()

    visitor_id = st.session_state["current_visitor_id"]
    visitor = get_visitor(visitor_id)

    st.title("Capture Visitor Photo")

    st.write(f"Name: {visitor['full_name']}")
    st.write(f"From: {visitor['from_company']}")
    st.write(f"To Meet: {visitor['person_to_meet']}")

    photo = st.camera_input("Capture Photo", help="Ensure face is visible")

    if st.button("Save & Generate Pass"):
        if not photo:
            st.error("Please capture the photo first")
            return

        photo_bytes = photo.getvalue()

        with st.spinner("Saving visitor pass"):
            # 1 Save to S3
            url = upload_photo(visitor, photo_bytes)

            # 2 Insert into visitor_identity
            insert_identity_record(visitor_id, url)

            # 3 Mark pass generated
            mark_pass_generated(visitor_id)

        st.success("Visitor pass generated")
        render_pass(visitor, photo_bytes)

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("New Visitor"):
                st.session_state.pop("current_visitor_id", None)
                st.session_state["visitor_data"] = {}
                st.session_state["registration_step"] = "primary"
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
