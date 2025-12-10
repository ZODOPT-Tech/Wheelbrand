import streamlit as st
import mysql.connector
import boto3
import json
import base64
import smtplib
from email.message import EmailMessage
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import pytz
import requests


# ======================================================
# CONFIG
# ======================================================
AWS_REGION = "ap-south-1"
AWS_SECRET_ARN = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
S3_BUCKET = "zodoptvisiorsmanagement"
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
IST = pytz.timezone("Asia/Kolkata")


# ======================================================
# AWS Secrets
# ======================================================
@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    res = client.get_secret_value(SecretId=AWS_SECRET_ARN)
    return json.loads(res["SecretString"])


# ======================================================
# DB Connection
# ======================================================
def db_conn():
    c = get_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True,
    )


# ======================================================
# Fetch Visitor
# ======================================================
def get_visitor(visitor_id):
    conn = db_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM visitors WHERE visitor_id=%s", (visitor_id,))
    data = cur.fetchone()
    cur.close()
    conn.close()
    return data


# ======================================================
# Save Photo and Update DB
# ======================================================
def save_photo_and_update(visitor, photo_bytes):
    s3 = boto3.client("s3")

    filename = (
        f"visitor_photos/"
        f"{visitor['from_company'].replace(' ', '_').lower()}/"
        f"{visitor['full_name'].replace(' ', '_').lower()}_"
        f"{int(datetime.now().timestamp())}.jpg"
    )

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=filename,
        Body=photo_bytes,
        ContentType="image/jpeg",
    )

    photo_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"

    conn = db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO visitor_identity (visitor_id, photo_url) VALUES (%s,%s)",
        (visitor["visitor_id"], photo_url),
    )
    cur.execute(
        "UPDATE visitors SET pass_generated=1, status='approved' WHERE visitor_id=%s",
        (visitor["visitor_id"],),
    )
    cur.close()
    conn.close()
    return photo_url


# ======================================================
# Generate Visitor Pass Image
# ======================================================
def generate_pass_image(visitor, photo_bytes):

    card = Image.new("RGB", (700, 900), "white")
    draw = ImageDraw.Draw(card)

    # Load fonts (system-safe)
    try:
        font_title = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50
        )
        font_text = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32
        )
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()

    # Logo
    try:
        logo_data = requests.get(LOGO_URL).content
        logo = Image.open(BytesIO(logo_data)).resize((180, 55))
        card.paste(logo, (260, 40))
    except:
        pass

    # Title
    draw.text((240, 120), "Visitor Pass", fill="#4B2ECF", font=font_title)

    # Photo
    face = Image.open(BytesIO(photo_bytes)).resize((280, 280))
    card.paste(face, (210, 200))

    # Info
    y = 520
    info = [
        ("Name", visitor["full_name"]),
        ("Company", visitor["from_company"]),
        ("To Meet", visitor["person_to_meet"]),
        ("Visitor ID", f"#{visitor['visitor_id']}"),
        ("Email", visitor["email"]),
        ("Date", datetime.now(IST).strftime("%d-%m-%Y %H:%M")),
    ]

    for key, val in info:
        draw.text((160, y), f"{key}: {val}", fill="black", font=font_text)
        y += 55

    out = BytesIO()
    card.save(out, format="JPEG")
    return out.getvalue()


# ======================================================
# Email with pass
# ======================================================
def send_email(visitor, pass_image):
    creds = get_credentials()

    msg = EmailMessage()
    msg["Subject"] = f"Visitor Pass - {visitor['full_name']}"
    msg["From"] = creds["SMTP_USER"]
    msg["To"] = visitor["email"]

    msg.set_content(f"""
Hello {visitor['full_name']},

Your Visitor Pass has been generated.

Visitor ID : {visitor['visitor_id']}
To Meet    : {visitor['person_to_meet']}
Date       : {datetime.now(IST).strftime("%d-%m-%Y %H:%M")}

Visitor pass attached.

Regards,
Reception
""")

    msg.add_attachment(
        pass_image,
        maintype="image",
        subtype="jpeg",
        filename="visitor_pass.jpg",
    )

    try:
        with smtplib.SMTP(creds["SMTP_HOST"], int(creds["SMTP_PORT"])) as server:
            server.starttls()
            server.login(creds["SMTP_USER"], creds["SMTP_PASSWORD"])
            server.send_message(msg)
        return True
    except:
        return False


# ======================================================
# Identity Page
# ======================================================
def render_identity_page():
    if not st.session_state.get("admin_logged_in"):
        st.session_state["current_page"] = "visitor_login"
        st.rerun()

    vid = st.session_state.get("current_visitor_id")
    visitor = get_visitor(vid)

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
        send_email(visitor, pass_image)

        st.session_state["pass_data"] = visitor
        st.session_state["pass_image"] = pass_image

        st.session_state["current_page"] = "visitor_pass"
        st.rerun()


# ======================================================
# Pass Page
# ======================================================
def render_pass_page():

    visitor = st.session_state.get("pass_data")
    img = st.session_state.get("pass_image")

    if not visitor or not img:
        st.error("No pass data found.")
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    col_pass, col_btn = st.columns([3, 1.3])

    # ---------- Pass (Left)
    with col_pass:
        st.markdown("""
        <style>
        .pass-card {
            background:white;
            padding:16px;
            border-radius:14px;
            box-shadow:0 4px 15px rgba(0,0,0,0.12);
            width:450px;
            margin-left:auto;
        }
        </style>
        """, unsafe_allow_html=True)

        b64 = base64.b64encode(img).decode()

        st.markdown("<div class='pass-card'>", unsafe_allow_html=True)
        st.markdown(f"<img src='data:image/jpeg;base64,{b64}' style='width:100%;border-radius:12px;'>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- Buttons (Right)
    with col_btn:
        st.markdown("""
        <style>
        .xbtn button {
            background:linear-gradient(90deg,#4B2ECF,#7A42FF) !important;
            color:white !important;
            border:none !important;
            font-weight:700 !important;
            font-size:16px !important;
            width:100% !important;
            border-radius:8px !important;
            margin-bottom:12px !important;
            padding:12px !important;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("<div class='xbtn'>", unsafe_allow_html=True)
        if st.button("📊 Dashboard"):
            st.session_state["current_page"] = "visitor_dashboard"
            st.rerun()

        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.session_state["current_page"] = "visitor_login"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
