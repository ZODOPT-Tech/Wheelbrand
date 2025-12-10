import streamlit as st
import mysql.connector
import boto3
import json
import base64
import smtplib
from email.message import EmailMessage
from datetime import datetime

# ======================================================
# CONFIG
# ======================================================
AWS_REGION = "ap-south-1"
AWS_SECRET_ARN = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
S3_BUCKET = "zodoptvisiorsmanagement"


# ======================================================
# SECRETS MANAGER
# ======================================================
@st.cache_resource
def get_credentials():
    """Fetch secret credentials from AWS Secrets Manager."""
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    raw = client.get_secret_value(SecretId=AWS_SECRET_ARN)
    return json.loads(raw["SecretString"])


# ======================================================
# DB Connection
# ======================================================
def db_conn():
    """Always return fresh DB connection."""
    c = get_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True
    )


# ======================================================
# Fetch Visitor Details
# ======================================================
def get_visitor(visitor_id: int):
    """Get visitor details from DB."""
    conn = db_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM visitors WHERE visitor_id=%s", (visitor_id,))
    data = cur.fetchone()

    cur.close()
    conn.close()
    return data


# ======================================================
# Upload Photo & Update DB
# ======================================================
def save_photo_and_update(visitor: dict, photo_bytes: bytes) -> str:
    """Upload visitor photo to S3 and update DB."""
    s3 = boto3.client("s3")

    filename = (
        f"visitor_photos/"
        f"{visitor['from_company'].replace(' ', '_').lower()}/"
        f"{visitor['full_name'].replace(' ', '_').lower()}_"
        f"{int(datetime.now().timestamp())}.jpg"
    )

    # upload to S3
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=filename,
        Body=photo_bytes,
        ContentType="image/jpeg"
    )

    photo_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"

    # update DB
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
    conn.close()
    return photo_url


# ======================================================
# Send Email
# ======================================================
def send_email(visitor: dict) -> bool:
    """Send visitor pass email."""
    creds = get_credentials()
    receiver = visitor.get("email")

    if not receiver:
        return False

    msg = EmailMessage()
    msg["Subject"] = f"Visitor Pass - {visitor['full_name']}"
    msg["From"] = creds["SMTP_USER"]
    msg["To"] = receiver

    msg.set_content(f"""
Hello {visitor['full_name']},

Welcome to {visitor['from_company']}!

✔ Your Visitor Pass has been generated.

Visitor ID : {visitor['visitor_id']}
To Meet    : {visitor['person_to_meet']}
Date       : {datetime.now().strftime("%d-%m-%Y %H:%M")}

Thanks,
Reception
""")

    try:
        with smtplib.SMTP(creds["SMTP_HOST"], int(creds["SMTP_PORT"])) as server:
            server.starttls()
            server.login(creds["SMTP_USER"], creds["SMTP_PASSWORD"])
            server.send_message(msg)
        return True

    except Exception as e:
        st.error("❌ Failed to send email.")
        st.error(str(e))
        return False


# ======================================================
# UI – PASS SCREEN
# ======================================================
def show_pass_screen(visitor: dict, photo_bytes: bytes):
    st.markdown(
        "<h2 style='text-align:center;color:#4B2ECF;'>Visitor Pass</h2>",
        unsafe_allow_html=True
    )

    img_data = base64.b64encode(photo_bytes).decode()

    card = f"""
    <div style="
        width:420px;margin:auto;background:white;
        border-radius:14px;padding:20px;
        box-shadow:0 4px 18px rgba(0,0,0,0.12);
    ">
        <div style="text-align:center;">
            <img src="data:image/jpeg;base64,{img_data}"
                 style="width:150px;height:150px;border-radius:12px;
                 border:4px solid #4B2ECF;">
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
    """
    st.markdown(card, unsafe_allow_html=True)

    st.write("")
    _, col_dash, col_out, _ = st.columns([1, 2, 2, 1])

    if col_dash.button("📊 Dashboard", use_container_width=True):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    if col_out.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.session_state["current_page"] = "visitor_login"
        st.rerun()


# ======================================================
# Capture Identity Page
# ======================================================
def render_identity_page():
    if not st.session_state.get("admin_logged_in", False):
        st.session_state["current_page"] = "visitor_login"
        st.rerun()

    vid = st.session_state.get("current_visitor_id")
    if not vid:
        st.session_state["current_page"] = "visitor_details"
        st.rerun()

    visitor = get_visitor(vid)
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
            st.error("Please capture a photo first.")
            return

        photo_bytes = photo.getvalue()

        save_photo_and_update(visitor, photo_bytes)

        if not send_email(visitor):
            return

        st.session_state["visitor_photo_bytes"] = photo_bytes
        st.session_state["current_page"] = "visitor_pass"
        st.rerun()


# ======================================================
# Pass Page Router
# ======================================================
def render_pass_page():
    visitor = get_visitor(st.session_state["current_visitor_id"])
    photo_bytes = st.session_state.get("visitor_photo_bytes")

    if not (visitor and photo_bytes):
        st.error("Unable to display pass.")
        return

    show_pass_screen(visitor, photo_bytes)
