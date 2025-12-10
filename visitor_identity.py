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
# Save photo & update DB
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
        "UPDATE visitors SET pass_generated=1 WHERE visitor_id=%s",
        (visitor["visitor_id"],)
    )
    cur.close()
    conn.close()
    return photo_url


# ======================================================
# Generate Visitor Pass Image
# ======================================================
def generate_pass_image(visitor, photo_bytes):
    # Load main image
    face_img = Image.open(BytesIO(photo_bytes)).resize((260, 260))
    
    # Create white canvas
    w, h = 700, 1000
    card = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(card)

    # Fonts
    font_title = ImageFont.truetype("arial.ttf", 44)
    font_text = ImageFont.truetype("arial.ttf", 32)

    # Add Logo
    try:
        logo_raw = Image.open(BytesIO(boto3.client("s3").get_object(
            Bucket=S3_BUCKET,
            Key="logo.jpg"
        )['Body'].read())).resize((220, 80))
    except:
        logo_raw = Image.open(BytesIO(requests.get(LOGO_URL).content)).resize((220, 80))

    card.paste(logo_raw, (240, 40))

    # Title
    draw.text((200, 160), "Visitor Pass", fill="#4B2ECF", font=font_title)

    # Photo
    card.paste(face_img, (220, 240))

    # Text
    y = 540
    data = [
        ("Name", visitor['full_name']),
        ("Company", visitor['from_company']),
        ("To Meet", visitor['person_to_meet']),
        ("Visitor ID", f"#{visitor['visitor_id']}"),
        ("Date", datetime.now().strftime("%d-%m-%Y %H:%M")),
        ("Email", visitor['email']),
    ]

    for key, val in data:
        draw.text((140, y), f"{key}: {val}", font=font_text, fill=(0, 0, 0))
        y += 60

    # Return as bytes
    out = BytesIO()
    card.save(out, format="JPEG")
    return out.getvalue()


# ======================================================
# Email
# ======================================================
def send_email(visitor, pass_image: bytes):
    creds = get_credentials()
    
    msg = EmailMessage()
    msg["Subject"] = f"Visitor Pass - {visitor['full_name']}"
    msg["From"] = creds["SMTP_USER"]
    msg["To"] = visitor.get("email")

    msg.set_content(f"""
Hello {visitor['full_name']},
Welcome to {visitor['from_company']}!
Your Visitor Pass has been generated.

Visitor ID: {visitor['visitor_id']}
To Meet: {visitor['person_to_meet']}
Date: {datetime.now().strftime("%d-%m-%Y %H:%M")}

Your digital visitor pass is attached.

Thanks,
Reception
""")

    msg.add_attachment(
        pass_image,
        maintype="image",
        subtype="jpeg",
        filename="visitor_pass.jpg"
    )

    try:
        with smtplib.SMTP(creds["SMTP_HOST"], int(creds["SMTP_PORT"])) as server:
            server.starttls()
            server.login(creds["SMTP_USER"], creds["SMTP_PASSWORD"])
            server.send_message(msg)
        return True
    except:
        return False  # Do nothing — show pass anyway


# ======================================================
# UI PASS SCREEN
# ======================================================
def show_pass_screen(visitor, pass_image, photo_bytes):
    st.markdown(
        "<h2 style='text-align:center;color:#4B2ECF;'>Visitor Pass</h2>",
        unsafe_allow_html=True
    )

    img_data = base64.b64encode(pass_image).decode()

    card = f"""
    <div style="
        width:460px;margin:auto;background:white;
        border-radius:14px;padding:20px;
        box-shadow:0 4px 18px rgba(0,0,0,0.12);">
        <div style="text-align:center;">
            <img src="data:image/jpeg;base64,{img_data}"
                 style="width:300px;border-radius:12px;border:4px solid #4B2ECF;">
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
    visitor = get_visitor(vid)
    st.title("Capture Visitor Photo")

    photo = st.camera_input("Capture Photo")

    if st.button("Save & Generate Pass"):
        if not photo:
            st.error("Please capture a photo.")
            return

        photo_bytes = photo.getvalue()
        save_photo_and_update(visitor, photo_bytes)

        # generate image
        pass_image = generate_pass_image(visitor, photo_bytes)

        # send email (ignore failed)
        send_email(visitor, pass_image)

        st.session_state["pass_image"] = pass_image
        st.session_state["visitor_photo_bytes"] = photo_bytes
        st.session_state["current_page"] = "visitor_pass"
        st.rerun()


# ======================================================
# Pass Page Router
# ======================================================
def render_pass_page():
    visitor = get_visitor(st.session_state["current_visitor_id"])
    pass_image = st.session_state.get("pass_image")
    photo_bytes = st.session_state.get("visitor_photo_bytes")

    show_pass_screen(visitor, pass_image, photo_bytes)

