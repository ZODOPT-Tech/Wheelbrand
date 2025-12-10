import streamlit as st
from datetime import datetime
import mysql.connector
import boto3
import json


AWS_REGION = "ap-south-1"
AWS_BUCKET = "zodoptvisiorsmanagement"  # Updated Bucket Name
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


# ---------------- S3 UPLOAD ----------------
def upload_to_s3(file_bytes, filename, content_type):
    s3 = boto3.client("s3")  # IAM ROLE
    s3.put_object(
        Bucket=AWS_BUCKET,
        Key=filename,
        Body=file_bytes,
        ContentType=content_type
    )
    return f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"


# ---------------- SAVE TO DB ----------------
def save_identity(company_id, full_name, company_name, id_type, id_number, photo_url):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO visitor_identity (
            company_id, full_name, company_name,
            id_type, id_number, photo_url, captured_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        company_id,
        full_name,
        company_name,
        id_type,
        id_number,
        photo_url,
        datetime.now()
    ))

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
    company_name = st.session_state["company_name"]

    st.subheader("👤 Visitor Details")

    full_name = st.text_input("Visitor Full Name")
    
    id_type = st.selectbox(
        "Government ID Type",
        [
            "Aadhaar Card",
            "PAN Card",
            "Driving License",
            "Voter ID",
            "Passport",
            "Ration Card"
        ]
    )

    id_number = st.text_input("ID Number")

    st.write("---")

    col1, col2 = st.columns([1, 1])

    # --- PHOTO ---
    with col1:
        st.subheader("📸 Visitor Photo (Required)")
        camera_photo = st.camera_input("Take Photo", label_visibility="collapsed")


    st.write("")

    # ---------------- SUBMIT BUTTON ----------------
    st.markdown('<div class="btn-primary">', unsafe_allow_html=True)

    if st.button("Generate Visitor Pass →", use_container_width=True):

        if not full_name:
            st.error("Visitor name is required.")
            return

        if not id_number:
            st.error("ID Number is required.")
            return

        if camera_photo is None:
            st.error("Photo is required.")
            return

        with st.spinner("Saving visitor identity..."):

            # Save photo to S3
            bytes_photo = camera_photo.read()
            clean_name = full_name.replace(" ", "_")
            filename = f"visitorsphoto/{company_name}/{clean_name}_{datetime.now().timestamp()}.jpg"

            photo_url = upload_to_s3(bytes_photo, filename, "image/jpeg")

            # Save record in DB
            save_identity(
                company_id,
                full_name,
                company_name,
                id_type,
                id_number,
                photo_url
            )

        st.success("Visitor Pass Created Successfully!")
        st.balloons()

        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("⬅ Back to Dashboard"):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()


# EXPORT FOR ROUTER
def render_identity():
    return render_identity_page()


if __name__ == "__main__":
    st.session_state["company_id"] = 1
    st.session_state["company_name"] = "Test Company"
    render_identity_page()
