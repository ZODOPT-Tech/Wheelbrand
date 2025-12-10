import streamlit as st
import mysql.connector
import boto3
import json
import base64
import io
import smtplib
from email.message import EmailMessage
from datetime import datetime


# ======================================================
# AWS + DB CONFIG
# ======================================================
AWS_REGION = "ap-south-1"
AWS_SECRET_ARN = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
S3_BUCKET = "zodoptvisiorsmanagement"


@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    raw = client.get_secret_value(SecretId=AWS_SECRET_ARN)
    return json.loads(raw["SecretString"])


@st.cache_resource
def db_conn():
    c = get_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True
    )


# ======================================================
# DB Fetch
# ======================================================
def get_visitor(visitor_id):
    conn = db_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM visitors WHERE visitor_id=%s", (visitor_id,))
    data = cur.fetchone()
    cur.close()
    return data


# ======================================================
# Save Photo and DB Update
# ======================================================
def save_photo_and_update(visitor, photo_bytes):
    s3 = boto3.client("s3")

    name = visitor["full_name"].replace(" ", "_").lower()
    company = visitor["from_company"].replace(" ", "_").lower()
    filename = f"visitor_photos/{company}/{name}_{int(datetime.now().timestamp())}.jpg"

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=filename,
        Body=photo_bytes,
        ContentType="image/jpeg"
    )

    photo_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"

    conn = db_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO visitor_identity (visitor_id, photo_url) VALUES (%s,%s)",
        (visitor["visitor_id"], photo_url)
    )

    cur.execute(
        "UPDATE visitors SET pass_generated=1 WHERE visitor_id=%s",
        (visitor["visitor_id"],)
    )

    cur.close()
    return photo_url


# ======================================================
# Send Email
# ======================================================
def send_email(visitor):
    c = get_credentials()
    receiver = visitor.get("email")
    if not receiver:
        return False

    msg = EmailMessage()
    msg["Subject"] = f"Visitor Pass - {visitor['full_name']}"
    msg["From"] = c["SMTP_USER"]
    msg["To"] = receiver

    msg.set_content(f"""
Hello {visitor['full_name']},

Welcome to {visitor['from_company']}!

Your Visitor Pass has been generated.

Visitor ID : {visitor['visitor_id']}
To Meet    : {visitor['person_to_meet']}
Date       : {datetime.now().strftime("%d-%m-%Y %H:%M")}

Thank You,
Reception
""")

    try:
        server = smtplib.SMTP(c["SMTP_HOST"], int(c["SMTP_PORT"]))
        server.starttls()
        server.login(c["SMTP_USER"], c["SMTP_PASSWORD"])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email failed: {str(e)}")
        return False


# ======================================================
# UI – Show Pass Page
# ======================================================
def show_pass_screen(visitor, photo_bytes, sent):
    st.markdown("<h2 style='text-align:center;color:#4B2ECF;'>Visitor Pass</h2>", unsafe_allow_html=True)

    img_data = base64.b64encode(photo_bytes).decode()
    st.markdown(f"""
    <div style="
        width:420px;margin:auto;background:white;
        border-radius:14px;padding:20px;
        box-shadow:0 4px 18px rgba(0,0,0,0.12);
    ">
        <div style="text-align:center;">
            <img src="data:image/jpeg;base64,{img_data}"
            style="width:150px;height:150px;border-radius:12px;border:4px solid #4B2ECF;">
        </div>
        <div style="margin-top:15px;font-size:17px;">
            <p><b>Name:</b> {visitor['full_name']}</p>
            <p><b>Company:</b> {visitor['from_company']}</p>
            <p><b>To Meet:</b> {visitor['person_to_meet']}</p>
            <p><b>Visitor ID:</b> #{visitor['visitor_id']}</p>
            <p><b>Email Sent To:</b> {visitor['email']}</p>
            <p><b>Date:</b> {datetime.now().strftime("%d-%m-%Y %H:%M")}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if sent:
        st.success(f"Pass sent to email: {visitor['email']}")

    st.write("")
    st.write("")

    # CENTERED BUTTONS (only Dashboard & Logout)
    left_space, col_dash, col_out, right_space = st.columns([1, 2, 2, 1])

    with col_dash:
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state["current_page"] = "visitor_dashboard"
            st.rerun()

    with col_out:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.session_state["current_page"] = "visitor_login"
            st.rerun()


# ======================================================
# Identity Page
# ======================================================
def render_identity_page():
    if not st.session_state.get("admin_logged_in", False):
        st.session_state["current_page"] = "visitor_login"
        st.rerun()

    if "current_visitor_id" not in st.session_state:
        st.session_state["current_page"] = "visitor_details"
        st.rerun()

    visitor = get_visitor(st.session_state["current_visitor_id"])
    if not visitor:
        st.error("Visitor not found")
        return

    st.title("Capture Visitor Photo")

    st.write(f"**Name:** {visitor['full_name']}")
    st.write(f"**Company:** {visitor['from_company']}")
    st.write(f"**To Meet:** {visitor['person_to_meet']}")

    photo = st.camera_input("Capture Photo")

    if st.button("Save & Generate Pass"):
        if not photo:
            st.error("Please capture a photo first")
            return

        photo_bytes = photo.getvalue()
        save_photo_and_update(visitor, photo_bytes)
        sent = send_email(visitor)

        st.session_state["visitor_photo_bytes"] = photo_bytes
        st.session_state["pass_email_sent"] = sent
        st.session_state["current_page"] = "visitor_pass"
        st.rerun()


# ======================================================
# Pass Page Router
# ======================================================
def render_pass_page():
    visitor = get_visitor(st.session_state["current_visitor_id"])
    photo_bytes = st.session_state.get("visitor_photo_bytes")
    sent = st.session_state.get("pass_email_sent", False)
    show_pass_screen(visitor, photo_bytes, sent)
