import streamlit as st
from datetime import datetime
import mysql.connector
import boto3
import json
import base64
from streamlit_drawable_canvas import st_canvas


AWS_REGION = "ap-south-1"
AWS_BUCKET = "zodopt-visitor-identity"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"


# ---------------- AWS CREDENTIALS ----------------
@st.cache_resource
def get_aws_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    sec = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(sec["SecretString"])


# ---------------- MYSQL CONNECTION ----------------
@st.cache_resource
def get_connection():
    creds = get_aws_credentials()
    return mysql.connector.connect(
        host=creds["DB_HOST"],
        user=creds["DB_USER"],
        password=creds["DB_PASSWORD"],
        database=creds["DB_NAME"],
        autocommit=True,
    )


# ---------------- S3 UPLOAD (USING IAM ROLE) ----------------
def upload_to_s3(file_bytes, filename, content_type):
    s3 = boto3.client("s3")  # No keys needed – uses EC2 IAM role

    s3.put_object(
        Bucket=AWS_BUCKET,
        Key=filename,
        Body=file_bytes,
        ContentType=content_type
    )

    return f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"


# ---------------- SAVE TO DB ----------------
def save_identity(company_id, photo_url, signature_text):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO visitor_identity (company_id, photo_url, signature_text, captured_at)
        VALUES (%s, %s, %s, %s)
    """, (company_id, photo_url, signature_text, datetime.now()))

    cursor.close()


# ---------------- HEADER UI ----------------
def load_styles():
    st.markdown("""
        <style>
            .header-box {
                background: linear-gradient(90deg, #5036FF, #9C2CFF);
                padding: 22px;
                color: white;
                font-size: 26px;
                font-weight: 700;
                border-radius: 10px;
                margin-bottom: 25px;
            }
            .btn-primary button {
                background: linear-gradient(90deg, #5036FF, #9C2CFF) !important;
                color: white !important;
                border: none !important;
                padding: 12px !important;
                border-radius: 8px !important;
                font-size: 17px !important;
                font-weight: 600 !important;
            }
        </style>
    """, unsafe_allow_html=True)


# ---------------- MAIN PAGE ----------------
def render_identity_page():

    load_styles()

    st.markdown("""
        <div class="header-box">
            Visitor Identity Capture
        </div>
    """, unsafe_allow_html=True)

    company_id = st.session_state["company_id"]

    col1, col2 = st.columns([1, 1])

    # --- PHOTO ---
    with col1:
        st.subheader("📸 Visitor Photo (Optional)")
        camera_photo = st.camera_input("Take Photo", label_visibility="collapsed")

    # --- SIGNATURE ---
    with col2:
        st.subheader("✍️ Visitor Signature")
        canvas = st_canvas(
            stroke_width=3,
            stroke_color="#000000",
            background_color="#FFFFFF",
            height=200,
            width=480,
            drawing_mode="freedraw",
            key="signature",
        )

    st.write("")

    # ---------------- SUBMIT BUTTON ----------------
    st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
    if st.button("Generate Visitor Pass →", use_container_width=True):

        if canvas.image_data is None:
            st.error("Signature is required.")
            return

        with st.spinner("Saving visitor identity..."):

            # Photo upload only if captured
            photo_url = None
            if camera_photo:
                bytes_photo = camera_photo.read()
                filename = f"identity/company_{company_id}/{datetime.now().timestamp()}_photo.jpg"
                photo_url = upload_to_s3(bytes_photo, filename, "image/jpeg")

            # Convert signature to Base64 text
            signature_png = canvas.image_data
            signature_bytes = signature_png.tobytes()
            signature_text = base64.b64encode(signature_bytes).decode("utf-8")

            # Save record in DB
            save_identity(company_id, photo_url, signature_text)

        st.success("Visitor Pass Created Successfully!")
        st.balloons()

        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("⬅ Back to Dashboard"):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()
