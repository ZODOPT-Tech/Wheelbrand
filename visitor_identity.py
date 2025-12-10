import streamlit as st
import mysql.connector
import boto3
import json
from datetime import datetime
import base64
import smtplib
from email.mime.text import MIMEText


AWS_REGION = "ap-south-1"
SECRET_ID  = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
BUCKET     = "zodoptvisiorsmanagement"


# ==============================
# SECRET LOADER
# ==============================
@st.cache_resource
def get_secret():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    sec = client.get_secret_value(SecretId=SECRET_ID)
    return json.loads(sec["SecretString"])


# ==============================
# DB CONNECTION
# ==============================
@st.cache_resource
def get_db():
    cfg = get_secret()
    return mysql.connector.connect(
        host=cfg["DB_HOST"],
        user=cfg["DB_USER"],
        password=cfg["DB_PASSWORD"],
        database=cfg["DB_NAME"],
        autocommit=True
    )


# ==============================
# FETCH VISITOR
# ==============================
def fetch_visitor(visitor_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT visitor_id, full_name, email,
               from_company, person_to_meet
        FROM visitors WHERE visitor_id = %s
    """, (visitor_id,))
    row = cur.fetchone()
    cur.close()
    return row


# ==============================
# SMTP EMAIL
# ==============================
def send_email(visitor):
    sec = get_secret()

    host = sec["SMTP_HOST"]
    port = int(sec["SMTP_PORT"])
    user = sec["SMTP_USER"]
    pwd  = sec["SMTP_PASSWORD"]

    body = f"""
Hello {visitor['full_name']},

Your Visitor Pass is generated and approved.

Visitor ID: #{visitor['visitor_id']}
Company: {visitor['from_company']}
Meeting: {visitor['person_to_meet']}
Date: {datetime.now().strftime("%d-%m-%Y %H:%M")}

Thank you.
    """

    msg = MIMEText(body)
    msg["Subject"] = "Visitor Pass Generated"
    msg["From"] = user
    msg["To"]   = visitor["email"]

    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(user, pwd)
        s.send_message(msg)


# ==============================
# SAVE PHOTO TO S3 + DB
# ==============================
def save_photo(visitor, photo_bytes):
    folder = visitor["from_company"].lower()
    filename = f"{visitor['full_name'].replace(' ', '_')}_{visitor['visitor_id']}.jpg"

    s3 = boto3.client("s3")
    key = f"visitor_photos/{folder}/{filename}"

    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=photo_bytes,
        ContentType="image/jpeg"
    )

    url = f"https://{BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO visitor_identity(visitor_id, photo_url)
        VALUES(%s, %s)
    """, (visitor["visitor_id"], url))

    # update approved
    cur.execute("""
        UPDATE visitors
        SET status='approved', pass_generated=1
        WHERE visitor_id=%s
    """, (visitor["visitor_id"],))

    cur.close()
    return url


# ==============================
# PASS SCREEN
# ==============================
def render_pass_page():

    v = st.session_state["visitor"]
    st.title("Visitor Pass")

    st.markdown("""
    <div style="width:420px;margin:auto;background:white;
    border-radius:15px;padding:25px;text-align:center;
    box-shadow:0 3px 16px rgba(0,0,0,0.2);">
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <img src="{st.session_state['photo']}"
        style="width:130px;height:130px;border-radius:8px;
               border:2px solid #4B2ECF;margin-bottom:15px;">

        <p><b>Name:</b> {v['full_name']}</p>
        <p><b>Company:</b> {v['from_company']}</p>
        <p><b>To Meet:</b> {v['person_to_meet']}</p>
        <p><b>Visitor ID:</b> #{v['visitor_id']}</p>
        <p><b>Date:</b> {datetime.now().strftime("%d-%m-%Y %H:%M")}</p>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    
    if st.button("➕ New Visitor"):
        st.session_state.pop("visitor", None)
        st.session_state.pop("photo", None)
        st.session_state["current_page"] = "visitor_details"
        st.rerun()

    if st.button("📊 Dashboard"):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.session_state["current_page"] = "visitor_login"
        st.rerun()


# ==============================
# MAIN CAPTURE PAGE
# ==============================
def render_identity_page():

    vid = st.session_state.get("current_visitor_id")
    if not vid:
        st.session_state["current_page"] = "visitor_details"
        st.rerun()

    v = fetch_visitor(vid)

    st.title("Capture Identity")

    st.write(f"**Name:** {v['full_name']}")
    st.write(f"**Company:** {v['from_company']}")
    st.write(f"**Meeting:** {v['person_to_meet']}")

    photo = st.camera_input("Capture Photo")

    if st.button("Generate Pass"):
        if not photo:
            st.error("Please take a photo")
            return

        bytes_photo = photo.getvalue()

        url = save_photo(v, bytes_photo)
        st.session_state["photo"] = url
        st.session_state["visitor"] = v

        # send email
        if v["email"]:
            try:
                send_email(v)
            except Exception as e:
                st.warning(f"Email error: {e}")

        st.session_state["current_page"] = "visitor_pass"
        st.rerun()
