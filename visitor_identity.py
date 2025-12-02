import streamlit as st
from datetime import datetime
import mysql.connector
import boto3
import base64
from botocore.exceptions import ClientError
from streamlit_drawable_canvas import st_canvas

# ------------------ AWS CONFIG ------------------
AWS_REGION = "ap-south-1"
AWS_BUCKET = "zodopt-visitor-identity"   # change to your bucket name
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"


# ------------------ FETCH SECRET ------------------
@st.cache_resource
def get_aws_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    secret_json = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(secret_json["SecretString"])


# ------------------ MYSQL CONNECT ------------------
@st.cache_resource
def get_connection():
    creds = get_aws_credentials()
    return mysql.connector.connect(
        host=creds["DB_HOST"],
        user=creds["DB_USER"],
        password=creds["DB_PASSWORD"],
        database=creds["DB_NAME"],
        autocommit=True
    )


# ------------------ UPLOAD TO S3 ------------------
def upload_to_s3(file_bytes, filename, content_type):
    creds = get_aws_credentials()
    s3 = boto3.client(
        "s3",
        aws_access_key_id=creds["AWS_KEY"],
        aws_secret_access_key=creds["AWS_SECRET"],
        region_name=AWS_REGION
    )

    s3.put_object(
        Bucket=AWS_BUCKET,
        Key=filename,
        Body=file_bytes,
        ContentType=content_type
    )

    return f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"


# ------------------ SAVE TO DATABASE ------------------
def save_identity_record(company_id, photo_url, signature_url):
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        INSERT INTO visitor_identity
        (company_id, photo_url, signature_url, captured_at)
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(sql, (company_id, photo_url, signature_url, datetime.now()))
    cursor.close()


# ------------------ PAGE RENDER ------------------
def render_identity_page():

    if "company_id" not in st.session_state:
        st.error("Missing company session. Please login again.")
        st.stop()

    st.markdown("## 🆔 Identity Capture")
    st.info("Please capture your **live photo** and **digital signature** below.")

    company_id = st.session_state["company_id"]
    camera_photo = None
    signature_image = None

    # ------------------ CAMERA ------------------
    st.subheader("📸 Take Visitor Photo")
    camera_photo = st.camera_input("Capture Photo")

    # ------------------ SIGNATURE ------------------
    st.subheader("✍️ Visitor Signature")
    canvas = st_canvas(
        stroke_width=3,
        stroke_color="#000000",
        background_color="#FFFFFF",
        height=200,
        width=600,
        drawing_mode="freedraw",
        key="signature_canvas"
    )

    # ------------------ SUBMIT ------------------
    if st.button("Submit Identity →"):

        if camera_photo is None:
            st.error("Please capture a photo.")
            return

        if canvas.image_data is None:
            st.error("Please sign in the box.")
            return

        with st.spinner("Uploading..."):

            # ------- Upload Photo -------
            photo_bytes = camera_photo.read()
            photo_filename = f"identity/company_{company_id}/{datetime.now().timestamp()}_photo.jpg"
            photo_url = upload_to_s3(photo_bytes, photo_filename, "image/jpeg")

            # ------- Upload Signature -------
            signature_bytes = canvas.image_data.tobytes()
            sig_filename = f"identity/company_{company_id}/{datetime.now().timestamp()}_sign.png"
            signature_url = upload_to_s3(signature_bytes, sig_filename, "image/png")

            # ------- Save to DB -------
            save_identity_record(company_id, photo_url, signature_url)

        st.success("Identity Successfully Captured & Stored!")
        st.balloons()

        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    st.markdown("---")
    if st.button("⬅ Back to Dashboard"):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

