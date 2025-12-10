import streamlit as st
import mysql.connector
import boto3
import json
from datetime import datetime
import base64
import io
from PIL import Image as PILImage
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# =====================================================
# AWS CONFIG
# =====================================================
AWS_REGION = "ap-south-1"
AWS_BUCKET = "zodoptvisiorsmanagement"
AWS_SECRET_ARN = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"


# =====================================================
# DB Credentials
# =====================================================
@st.cache_resource
def get_db_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    secret = client.get_secret_value(SecretId=AWS_SECRET_ARN)
    return json.loads(secret["SecretString"])


@st.cache_resource
def get_db_conn():
    creds = get_db_credentials()
    return mysql.connector.connect(
        host=creds["DB_HOST"],
        user=creds["DB_USER"],
        password=creds["DB_PASSWORD"],
        database=creds["DB_NAME"],
        autocommit=True,
    )


# =====================================================
# Fetch Visitor Data
# =====================================================
def get_visitor_data(visitor_id):
    conn = get_db_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT visitor_id, full_name, email,
               from_company, person_to_meet,
               registration_timestamp
        FROM visitors
        WHERE visitor_id=%s
    """,
        (visitor_id,),
    )
    data = cur.fetchone()
    cur.close()
    return data


# =====================================================
# Upload Photo To S3
# =====================================================
def upload_photo_to_s3(visitor, photo_bytes):
    s3 = boto3.client("s3")

    company = visitor["from_company"]
    name = visitor["full_name"]

    folder_company = company.lower().replace(" ", "_")
    file_name = name.lower().replace(" ", "_")

    final_key = f"visitor_photos/{folder_company}/{file_name}_{int(datetime.now().timestamp())}.jpg"

    s3.put_object(
        Bucket=AWS_BUCKET,
        Key=final_key,
        Body=photo_bytes,
        ContentType="image/jpeg"
    )

    return f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{final_key}"


# =====================================================
# Save URL To visitor_identity
# =====================================================
def save_photo_url(visitor_id, photo_url):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO visitor_identity (visitor_id, photo_url) VALUES (%s,%s)",
        (visitor_id, photo_url)
    )
    conn.commit()
    cur.close()


# =====================================================
# Send Email (Zoho SMTP)
# =====================================================
def send_email_pass(visitor):
    secrets = get_db_credentials()

    receiver = visitor.get("email")
    if not receiver:
        return False

    subject = f"Your Visitor Pass - {visitor['full_name']}"

    body = f"""
    <h2 style='color:#4B2ECF;font-weight:700;'>Visitor Pass</h2>
    <p>Hello <b>{visitor['full_name']}</b>,</p>
    <p>Your visit is registered successfully.</p>
    <p><b>Visitor ID:</b> #{visitor['visitor_id']}</p>
    <p><b>Meeting:</b> {visitor['person_to_meet']}</p>
    <p><b>Date:</b> {datetime.now().strftime("%d-%m-%Y %H:%M")}</p>
    <br><br>
    <p>Thank you!</p>
    """

    msg = MIMEMultipart()
    msg["From"] = secrets["ZOHO_EMAIL_SENDER"]
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        server = smtplib.SMTP(secrets["ZOHO_SMTP_SERVER"], secrets["ZOHO_SMTP_PORT"])
        server.starttls()
        server.login(secrets["ZOHO_EMAIL_USER"], secrets["ZOHO_EMAIL_PASSWORD"])
        server.sendmail(secrets["ZOHO_EMAIL_SENDER"], receiver, msg.as_string())
        server.quit()
        return True
    except:
        return False


# =====================================================
# HTML Visitor Pass UI
# =====================================================
def show_pass(visitor, photo_bytes):

    b64 = base64.b64encode(photo_bytes).decode()

    st.markdown(
        f"""
        <div style="display:flex;justify-content:center;margin-top:10px;">
        <div style="
            width:420px;
            background:white;
            box-shadow:0 4px 14px rgba(0,0,0,0.13);
            border-radius:14px;
            padding:22px;">
            
            <h2 style="text-align:center;color:#4B2ECF;margin-bottom:14px;">VISITOR PASS</h2>
            
            <div style="text-align:center;margin-bottom:14px;">
                <img src="data:image/jpeg;base64,{b64}"
                    style="width:130px;height:130px;border-radius:10px; border:2px solid #4B2ECF;">
            </div>

            <p><b>Name:</b> {visitor['full_name']}</p>
            <p><b>Company:</b> {visitor['from_company']}</p>
            <p><b>To Meet:</b> {visitor['person_to_meet']}</p>
            <p><b>Visitor ID:</b> #{visitor['visitor_id']}</p>
            <p><b>Date:</b> {datetime.now().strftime("%d-%m-%Y %H:%M")}</p>
        </div>
        </div>
    """,
        unsafe_allow_html=True,
    )


# =====================================================
# MAIN ENTRY
# =====================================================
def render_identity_page():
    # Permission check
    if not st.session_state.get("admin_logged_in", False):
        st.session_state["current_page"] = "visitor_login"
        st.rerun()

    if "current_visitor_id" not in st.session_state:
        st.error("No visitor selected.")
        st.session_state["current_page"] = "visitor_details"
        st.rerun()

    visitor_id = st.session_state["current_visitor_id"]
    visitor = get_visitor_data(visitor_id)

    st.title("Take Photo & Generate Visitor Pass")
    st.write(f"**Name:** {visitor['full_name']}")
    st.write(f"**Company:** {visitor['from_company']}")
    st.write(f"**Meeting With:** {visitor['person_to_meet']}")

    photo = st.camera_input("Capture Photo", label_visibility="hidden")

    if st.button("Save & Generate Pass", use_container_width=True):
        if not photo:
            st.error("Please capture a photo first.")
            return

        photo_bytes = photo.getvalue()

        with st.spinner("Uploading photo..."):
            photo_url = upload_photo_to_s3(visitor, photo_bytes)
            save_photo_url(visitor_id, photo_url)

        with st.spinner("Sending Email..."):
            send_email_pass(visitor)

        with st.spinner("Updating status..."):
            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute(
                "UPDATE visitors SET status='approved', pass_generated=1 WHERE visitor_id=%s",
                (visitor_id,)
            )
            conn.commit()
            cur.close()

        st.success("Visitor Pass Generated & Email Sent!")
        show_pass(visitor, photo_bytes)

        st.write("")
        if st.button("➕ New Visitor", use_container_width=True):
            st.session_state.pop("current_visitor_id", None)
            st.session_state["current_page"] = "visitor_details"
            st.rerun()

        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state["current_page"] = "visitor_dashboard"
            st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.session_state["current_page"] = "visitor_login"
            st.rerun()

    if st.button("← Back", use_container_width=True):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()
