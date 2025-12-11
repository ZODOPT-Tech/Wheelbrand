import streamlit as st
import mysql.connector
import boto3
import json
import base64
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests


# ========================
# CONFIG
# ========================
AWS_REGION = "ap-south-1"
AWS_SECRET_ARN = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
S3_BUCKET = "zodoptvisiorsmanagement"
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"


# ========================
# SECRETS MANAGER
# ========================
@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    raw = client.get_secret_value(SecretId=AWS_SECRET_ARN)
    return json.loads(raw["SecretString"])


# ========================
# DATABASE CONNECTION
# ========================
def db_conn():
    creds = get_credentials()
    return mysql.connector.connect(
        host=creds["DB_HOST"],
        user=creds["DB_USER"],
        password=creds["DB_PASSWORD"],
        database=creds["DB_NAME"],
        autocommit=True
    )


# ========================
# FETCH VISITOR DATA
# ========================
def get_visitor(visitor_id: int):
    conn = db_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM visitors WHERE visitor_id=%s", (visitor_id,))
    data = cur.fetchone()
    cur.close()
    conn.close()
    return data


# ========================
# SAVE PHOTO TO S3 + UPDATE DB
# ========================
def save_photo_and_update(visitor, photo_bytes):
    s3 = boto3.client("s3")
    filename = (
        f"visitor_photos/{visitor['from_company'].replace(' ', '_').lower()}/"
        f"{visitor['full_name'].replace(' ', '_').lower()}_"
        f"{int(datetime.now().timestamp())}.jpg"
    )

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
        "INSERT INTO visitor_identity (visitor_id, photo_url) VALUES (%s, %s)",
        (visitor["visitor_id"], photo_url)
    )
    cur.execute(
        "UPDATE visitors SET pass_generated=1, status='approved' WHERE visitor_id=%s",
        (visitor["visitor_id"],)
    )
    cur.close()
    conn.close()
    return photo_url


# ========================
# GENERATE VISITOR PASS IMAGE
# ========================
def generate_pass_image(visitor, photo_bytes):
    face_img = Image.open(BytesIO(photo_bytes)).resize((230, 230))
    W, H = 700, 1000
    card = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(card)

    # Fonts
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()

    # Logo
    try:
        logo_data = requests.get(LOGO_URL).content
        logo = Image.open(BytesIO(logo_data)).resize((200, 60))
        card.paste(logo, (250, 40))
    except:
        pass

    draw.text((230, 140), "Visitor Pass", fill="#4B2ECF", font=font_title)
    card.paste(face_img, (235, 220))

    y = 500
    info = [
        ("Name", visitor["full_name"]),
        ("Company", visitor["from_company"]),
        ("To Meet", visitor["person_to_meet"]),
        ("Visitor ID", f"#{visitor['visitor_id']}"),
        ("Email", visitor["email"]),
        ("Date", datetime.now().strftime("%d-%m-%Y %H:%M")),
    ]

    for key, val in info:
        draw.text((140, y), f"{key}: {val}", font=font_text, fill="black")
        y += 60

    out = BytesIO()
    card.save(out, format="JPEG")
    return out.getvalue()


# ========================
# SEND EMAIL (Zoho or Google SMTP)
# ========================
def send_email(visitor, pass_image):
    creds = get_credentials()

    sender_email = creds["SMTP_USER"]
    sender_password = creds["SMTP_PASSWORD"]
    smtp_host = creds["SMTP_HOST"]
    smtp_port = int(creds["SMTP_PORT"])
    receiver_email = visitor["email"]

    subject = f"Visitor Pass - {visitor['full_name']}"
    body = f"""
Hello {visitor['full_name']},

Your Visitor Pass has been generated.

Visitor ID : {visitor['visitor_id']}
To Meet    : {visitor['person_to_meet']}
Date       : {datetime.now().strftime("%d-%m-%Y %H:%M")}

Your visitor pass is attached.

Thank You,
Reception
"""

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    attachment = MIMEApplication(pass_image, _subtype="jpeg")
    attachment.add_header("Content-Disposition", "attachment", filename="visitor_pass.jpg")
    msg.attach(attachment)

    server = None
    try:
        # Use TLS if port 587, SSL if port 465
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.starttls()

        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        logging.info(f"[VISITOR PASS] Email sent to {receiver_email}")
        return True, None

    except smtplib.SMTPAuthenticationError:
        return False, "SMTP Authentication Failed (Check App Password)"
    except Exception as e:
        return False, str(e)
    finally:
        if server:
            try:
                server.quit()
            except:
                pass


# ========================
# RENDER IDENTITY PAGE
# ========================
def render_identity_page():
    if not st.session_state.get("admin_logged_in"):
        st.session_state["current_page"] = "visitor_login"
        st.rerun()

    visitor_id = st.session_state.get("current_visitor_id")
    visitor = get_visitor(visitor_id)

    st.title("Capture Visitor Photo")
    st.write(f"**Name:** {visitor['full_name']}")
    st.write(f"**Company:** {visitor['from_company']}")
    st.write(f"**To Meet:** {visitor['person_to_meet']}")

    photo = st.camera_input("Capture Photo")

    if st.button("Save & Generate Pass"):
        if not photo:
            st.error("Please capture a photo.")
            return

        photo_bytes = photo.getvalue()
        save_photo_and_update(visitor, photo_bytes)
        pass_image = generate_pass_image(visitor, photo_bytes)
        sent, err = send_email(visitor, pass_image)

        if sent:
            st.success(f"Email sent to {visitor['email']}")
        else:
            st.error(f"Email failed: {err}")

        st.session_state["pass_data"] = visitor
        st.session_state["pass_image"] = pass_image
        st.session_state["current_page"] = "visitor_pass"
        st.rerun()


# ========================
# RENDER PASS PAGE
# ========================
def render_pass_page():
    visitor = st.session_state.get("pass_data")
    pass_image = st.session_state.get("pass_image")

    if not visitor or not pass_image:
        st.error("No pass data found.")
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    st.markdown("<h2 style='text-align:center;color:#4B2ECF;'>Visitor Pass</h2>", unsafe_allow_html=True)

    img_data = base64.b64encode(pass_image).decode()
    st.markdown(f"""
    <div style="width:480px;margin:auto;background:white;border-radius:14px;padding:20px;
                box-shadow:0 4px 18px rgba(0,0,0,0.12);text-align:center;">
        <img src="data:image/jpeg;base64,{img_data}"
             style="width:330px;border-radius:12px;border:4px solid #4B2ECF;">
    </div>
    """, unsafe_allow_html=True)

    _, col1, col2, _ = st.columns([1,2,2,1])
    if col1.button("📊 Dashboard", use_container_width=True):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    if col2.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.session_state["current_page"] = "visitor_login"
        st.rerun()
