import streamlit as st
from datetime import datetime
import mysql.connector
import boto3
import json
from botocore.exceptions import ClientError
from streamlit_drawable_canvas import st_canvas

# ------------------ AWS CONFIG ------------------
AWS_REGION = "ap-south-1"
AWS_BUCKET = "zodopt-visitor-identity"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"


# ------------------ STYLES ------------------
def load_styles():
    st.markdown("""
        <style>
            .header-box {
                background: linear-gradient(90deg, #5036FF, #9C2CFF);
                padding: 25px;
                border-radius: 12px;
                color: white;
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 25px;
            }
            .sub-text {
                font-size: 15px;
                opacity: 0.9;
                font-weight: 400;
            }
            .primary-btn button {
                background: linear-gradient(90deg, #5036FF, #9C2CFF) !important;
                border: none !important;
                color: white !important;
                border-radius: 8px !important;
                padding: 12px !important;
                font-size: 17px !important;
                font-weight: 600 !important;
            }
        </style>
    """, unsafe_allow_html=True)


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

    load_styles()

    if "company_id" not in st.session_state:
        st.error("Missing company session. Please login again.")
        st.stop()

    company_id = st.session_state["company_id"]

    # ------------------ HEADER ------------------
    st.markdown("""
        <div class="header-box">
            Identity Verification
            <div class="sub-text">Capture live photo & digital signature</div>
        </div>
    """, unsafe_allow_html=True)

    # ------------------ AUTO TRIGGER CAMERA PERMISSION ------------------
    st.markdown("""
        <script>
            // Trigger camera permission request on load
            setTimeout(() => {
                const el = window.parent.document.querySelector('input[type="file"][accept="image/*"]');
                if (el) { el.click(); }
            }, 500);
        </script>
    """, unsafe_allow_html=True)

    # ------------------ CAMERA (FIRST) ------------------
    st.subheader("📸 Take Visitor Photo")
    camera_photo = st.camera_input("Camera Preview")  # triggers native Chrome allow popup

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

    # ------------------ SUBMIT BUTTON ------------------
    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)

    if st.button("Submit Identity →", use_container_width=True):

        if camera_photo is None:
            st.error("Please capture a photo.")
            return

        if canvas.image_data is None:
            st.error("Please provide a signature.")
            return

        with st.spinner("Uploading..."):

            # Upload Photo
            photo_bytes = camera_photo.read()
            file_photo = f"identity/company_{company_id}/{datetime.now().timestamp()}_photo.jpg"
            photo_url = upload_to_s3(photo_bytes, file_photo, "image/jpeg")

            # Upload Signature
            sig_bytes = canvas.image_data.tobytes()
            file_sig = f"identity/company_{company_id}/{datetime.now().timestamp()}_sign.png"
            signature_url = upload_to_s3(sig_bytes, file_sig, "image/png")

            # Save to DB
            save_identity_record(company_id, photo_url, signature_url)

        st.success("Identity Successfully Captured!")
        st.balloons()

        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    if st.button("⬅ Back to Dashboard"):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()
