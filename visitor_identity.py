import streamlit as st
from datetime import datetime
import mysql.connector
import boto3
import json
from streamlit_drawable_canvas import st_canvas

AWS_REGION = "ap-south-1"
AWS_BUCKET = "zodopt-visitor-identity"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"


# -------- Styles --------
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

            .identity-container {
                background: white;
                padding: 25px;
                border-radius: 14px;
                box-shadow: 0px 4px 18px rgba(0,0,0,0.07);
                max-width: 700px;
                margin: auto;
            }

            /* Camera Placeholder Box */
            .camera-placeholder {
                width: 420px;
                height: 260px;
                background: #F4F4F8;
                border-radius: 12px;
                display: flex;
                justify-content: center;
                align-items: center;
                color: #777;
                font-size: 17px;
                margin: auto;
                border: 2px dashed #C8C8D2;
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


# -------- AWS Credentials --------
@st.cache_resource
def get_aws_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    sec = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(sec["SecretString"])


# -------- DB Connection --------
@st.cache_resource
def get_connection():
    creds = get_aws_credentials()
    return mysql.connector.connect(
        host=creds["DB_HOST"], user=creds["DB_USER"],
        password=creds["DB_PASSWORD"], database=creds["DB_NAME"],
        autocommit=True
    )


# -------- Upload to S3 --------
def upload_to_s3(file_bytes, filename, content_type):
    creds = get_aws_credentials()
    s3 = boto3.client(
        "s3",
        aws_access_key_id=creds["AWS_KEY"],
        aws_secret_access_key=creds["AWS_SECRET"],
        region_name=AWS_REGION
    )
    s3.put_object(Bucket=AWS_BUCKET, Key=filename, Body=file_bytes, ContentType=content_type)
    return f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"


# -------- Save to DB --------
def save_identity(company_id, photo_url, sign_url):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO visitor_identity 
           (company_id, photo_url, signature_url, captured_at)
           VALUES (%s, %s, %s, %s)""",
        (company_id, photo_url, sign_url, datetime.now())
    )
    cur.close()


# -------- Render UI --------
def render_identity_page():

    load_styles()

    st.markdown("""
        <div class="header-box">
            Identity Verification
            <div style="font-size:14px;opacity:0.85;">Capture photo & signature</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="identity-container">', unsafe_allow_html=True)

    st.subheader("📸 Visitor Photo")

    camera_col, _ = st.columns([1, 1])

    with camera_col:

        # ------- CLEAN PLACEHOLDER BEFORE CAMERA LOAD -------
        ph = st.empty()

        with ph.container():
            st.markdown("""
                <div class="camera-placeholder">
                    Click 'Allow' on your browser to open camera
                </div>
            """, unsafe_allow_html=True)

        # ------- CAMERA LOAD (Chrome will ask permission) -------
        camera_photo = st.camera_input("", label_visibility="collapsed")

        # Remove placeholder after permission
        if camera_photo:
            ph.empty()

    st.subheader("✍️ Visitor Signature")
    canvas = st_canvas(
        stroke_width=3,
        stroke_color="#000000",
        background_color="#FFFFFF",
        height=180,
        width=600,
        drawing_mode="freedraw",
        key="sign_canvas"
    )

    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
    if st.button("Submit Identity →", use_container_width=True):

        if not camera_photo:
            st.error("Please take a photo.")
            return

        if canvas.image_data is None:
            st.error("Please sign.")
            return

        with st.spinner("Uploading..."):

            cid = st.session_state["company_id"]

            # UPLOAD PHOTO
            photo_bytes = camera_photo.read()
            p_name = f"identity/company_{cid}/{datetime.now().timestamp()}_photo.jpg"
            p_url = upload_to_s3(photo_bytes, p_name, "image/jpeg")

            # UPLOAD SIGNATURE
            sig_bytes = canvas.image_data.tobytes()
            s_name = f"identity/company_{cid}/{datetime.now().timestamp()}_sign.png"
            s_url = upload_to_s3(sig_bytes, s_name, "image/png")

            save_identity(cid, p_url, s_url)

        st.success("Identity captured successfully!")
        st.balloons()
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
