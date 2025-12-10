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


# ======================================================
# CONFIG
# ======================================================
AWS_REGION = "ap-south-1"
AWS_SECRET_ARN = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
S3_BUCKET = "zodoptvisiorsmanagement"
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"


# ======================================================
# SECRETS MANAGER
# ======================================================
@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    raw = client.get_secret_value(SecretId=AWS_SECRET_ARN)
    return json.loads(raw["SecretString"])


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
        autocommit=True
    )


# ======================================================
# Fetch Visitor Details
# ======================================================
def get_visitor(visitor_id: int):
    conn = db_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM visitors WHERE visitor_id=%s", (visitor_id,))
    data = cur.fetchone()
    cur.close()
    conn.close()
    return data


# ======================================================
# Save photo + DB update
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
        "UPDATE visitors SET pass_generated=1, status='approved' WHERE visitor_id=%s",
        (visitor["visitor_id"],)
    )
    cur.close()
    conn.close()
    return photo_url


# ======================================================
# Visitor Pass Image Generation
# ======================================================
def generate_pass_image(visitor, photo_bytes):

    face_img = Image.open(BytesIO(photo_bytes)).resize((230, 230))

    W, H = 700, 1000
    card = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(card)

    # Fonts
    try:
        font_title = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48
        )
        font_text = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32
        )
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()

    # Logo
    try:
        import requests
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


# ======================================================
# Email with Attachment (Gmail SMTP)
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
Date       : {datetime.now().strftime("%d-%m-%Y %H:%M")}

Your visitor pass is attached as an image.

Thank You,
Reception
""")

    msg.add_attachment(
        pass_image,
        maintype="image",
        subtype="jpeg",
        filename="visitor_pass.jpg"
    )

    try:
        smtp_server = creds["SMTP_HOST"]
        smtp_port = int(creds["SMTP_PORT"])
        smtp_user = creds["SMTP_USER"]
        smtp_pwd = creds["SMTP_PASSWORD"]

        # Gmail SMTP
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pwd)
            server.send_message(msg)

        return True

    except Exception as e:
        print("Email send failed:", e)
        return False


# ======================================================
# IDENTITY PAGE UI
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

        st.session_state["pass_data"] = {
            "visitor_id": visitor["visitor_id"],
            "full_name": visitor["full_name"],
            "from_company": visitor["from_company"],
            "person_to_meet": visitor["person_to_meet"],
            "email": visitor["email"],
            "photo_bytes": photo_bytes,
        }
        st.session_state["pass_image"] = pass_image

        st.session_state["current_page"] = "visitor_pass"
        st.rerun()


# ======================================================
# PASS SCREEN UI
# ======================================================
def render_pass_page():

    visitor = st.session_state.get("pass_data")
    pass_image = st.session_state.get("pass_image")

    if not visitor or not pass_image:
        st.error("Data not found.")
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    st.markdown(
        "<h2 style='text-align:center;color:#4B2ECF;'>Visitor Pass</h2>",
        unsafe_allow_html=True,
    )

    img_data = base64.b64encode(pass_image).decode()

    st.markdown(
        f"""
    <div style="
        width:480px;margin:auto;background:white;
        border-radius:14px;padding:20px;
        box-shadow:0 4px 18px rgba(0,0,0,0.12);
    ">
        <div style="text-align:center;">
            <img src="data:image/jpeg;base64,{img_data}"
                 style="width:330px;border-radius:12px;border:4px solid #4B2ECF;">
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    _, col_dash, col_out, _ = st.columns([1, 2, 2, 1])

    if col_dash.button("📊 Dashboard", use_container_width=True):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    if col_out.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.session_state["current_page"] = "visitor_login"
        st.rerun()
