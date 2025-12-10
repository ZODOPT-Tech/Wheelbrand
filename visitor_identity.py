import streamlit as st
import mysql.connector
import boto3
import json
from datetime import datetime
import io
import base64

AWS_REGION = "ap-south-1"
AWS_BUCKET = "zodoptvisiorsmanagement"
AWS_SECRET_ARN = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
FOLDER_NAME = "visitor_photos"


# ----------------------- DB Credentials -----------------------
@st.cache_resource
def get_db_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    sec = client.get_secret_value(SecretId=AWS_SECRET_ARN)
    return json.loads(sec["SecretString"])


@st.cache_resource
def get_db_conn():
    c = get_db_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True,
    )


# ----------------------- AWS Upload -----------------------
def upload_photo(visitor, photo_bytes):
    s3 = boto3.client("s3")

    # normalize folder names
    company = visitor["from_company"].strip().lower().replace(" ", "_")
    name = visitor["full_name"].strip().lower().replace(" ", "_")

    ts = int(datetime.now().timestamp())
    key = f"{FOLDER_NAME}/{company}/{name}_{ts}.jpg"

    s3.put_object(
        Bucket=AWS_BUCKET,
        Key=key,
        Body=photo_bytes,
        ContentType="image/jpeg"
    )

    photo_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
    return photo_url


# ----------------------- DB Update -----------------------
def save_photo_url(visitor_id, photo_url):
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE visitors
        SET photo_url = %s
        WHERE visitor_id = %s
        """,
        (photo_url, visitor_id),
    )
    cur.close()


# ----------------------- Get Visitor -----------------------
def get_visitor_data(visitor_id):
    conn = get_db_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT 
            visitor_id,
            full_name,
            from_company,
            person_to_meet,
            visit_type,
            registration_timestamp
        FROM visitors
        WHERE visitor_id = %s
    """, (visitor_id,))

    data = cur.fetchone()
    cur.close()
    return data


# ----------------------- CSS -----------------------
def load_css():
    st.markdown("""
        <style>
        .pass-box {
            width:420px;
            margin:auto;
            margin-top:30px;
            padding:22px;
            background:white;
            border-radius:16px;
            box-shadow:0 6px 22px rgba(0,0,0,0.12);
            text-align:left;
        }
        .pass-title {
            text-align:center;
            color:#5036FF;
            font-weight:800;
            font-size:32px;
            margin-bottom:20px;
        }
        .photo-box {
            text-align:center;
            margin-bottom:16px;
        }
        .photo-box img {
            width:120px;
            height:120px;
            border-radius:12px;
            border:2px solid #5036FF;
        }
        .label {
            font-weight:600;
        }
        .footer-btns {
            margin-top:24px;
        }
        .footer-btns button {
            font-size:16px !important;
            border-radius:8px !important;
        }
        </style>
    """, unsafe_allow_html=True)


# ----------------------- PASS UI -----------------------
def show_pass(visitor, photo_bytes):
    b64 = base64.b64encode(photo_bytes).decode()

    st.markdown(f"""
        <div class="pass-box">
            <div class="pass-title">VISITOR PASS</div>

            <div class="photo-box">
                <img src="data:image/jpeg;base64,{b64}">
            </div>

            <p><span class="label">Name:</span> {visitor['full_name']}</p>
            <p><span class="label">From:</span> {visitor['from_company']}</p>
            <p><span class="label">Meeting:</span> {visitor['person_to_meet']}</p>
            <p><span class="label">Visitor ID:</span> #{visitor['visitor_id']}</p>
            <p><span class="label">Date:</span> {datetime.now().strftime("%d-%m-%Y %H:%M")}</p>
        </div>
    """, unsafe_allow_html=True)


# ----------------------- MAIN PAGE -----------------------
def render_identity_page():

    # Auth Check
    if not st.session_state.get("admin_logged_in"):
        st.session_state["current_page"] = "visitor_login"
        st.rerun()

    if "current_visitor_id" not in st.session_state:
        st.session_state["current_page"] = "visitor_details"
        st.rerun()

    load_css()

    visitor_id = st.session_state["current_visitor_id"]
    visitor = get_visitor_data(visitor_id)

    st.markdown("<h2 style='text-align:center;font-size:38px;color:#5036FF;'>Identity Capture</h2>", unsafe_allow_html=True)

    # Camera
    photo = st.camera_input("Capture Visitor Photo", label_visibility="collapsed")

    st.write("")
    if st.button("Save & Generate Pass", use_container_width=True):
        if not photo:
            st.error("Please capture a photo.")
            return

        photo_bytes = photo.getvalue()

        # upload to S3
        photo_url = upload_photo(visitor, photo_bytes)

        # update DB
        save_photo_url(visitor_id, photo_url)

        st.success("Visitor Pass Created Successfully!")

        show_pass(visitor, photo_bytes)

        # Actions
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("New Visitor"):
                st.session_state.pop("current_visitor_id", None)
                st.session_state["current_page"] = "visitor_details"
                st.rerun()

        with c2:
            if st.button("Dashboard"):
                st.session_state["current_page"] = "visitor_dashboard"
                st.rerun()

        with c3:
            if st.button("Logout"):
                st.session_state.clear()
                st.session_state["current_page"] = "visitor_login"
                st.rerun()

    st.write("")
    if st.button("Back"):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()
