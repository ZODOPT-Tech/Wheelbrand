import streamlit as st
import mysql.connector
import boto3
import json
from datetime import datetime
import base64
import io

# ======================================================
# AWS + DB CONFIG
# ======================================================
AWS_REGION = "ap-south-1"
AWS_BUCKET = "zodoptvisiorsmanagement"
FOLDER_NAME = "visitor_photos"
AWS_SECRET_ARN = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

HEADER_GRADIENT = "linear-gradient(90deg, #4B2ECF, #7A42FF)"


# ---------------- AWS Secret ----------------
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


# ======================================================
# FETCH VISITOR DATA
# ======================================================
def get_visitor_data(visitor_id: int):
    conn = get_db_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT visitor_id, full_name, from_company, person_to_meet, registration_timestamp
        FROM visitors WHERE visitor_id=%s
    """, (visitor_id,))
    data = cur.fetchone()
    cur.close()
    return data


# ======================================================
# SAVE PHOTO to S3 + DB FLAG
# ======================================================
def save_photo(visitor_id, visitor_name, company_name, photo_bytes):
    s3 = boto3.client("s3")

    # normalize
    folder = company_name.lower().replace(" ", "_")
    name = visitor_name.lower().replace(" ", "_")

    filename = f"{FOLDER_NAME}/{folder}/{name}_{int(datetime.now().timestamp())}.jpg"

    # upload file
    s3.put_object(
        Bucket=AWS_BUCKET,
        Key=filename,
        Body=photo_bytes,
        ContentType="image/jpeg"
    )

    # URL
    url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{filename}"

    # DB save
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO visitor_identity (visitor_id, photo_url) VALUES (%s,%s)", (visitor_id, url))
    cursor.execute("UPDATE visitors SET status='approved', pass_generated=1 WHERE visitor_id=%s", (visitor_id,))
    cursor.close()

    return url


# ======================================================
# HEADER
# ======================================================
def load_styles():
    st.markdown(f"""
    <style>
        .title {{
            text-align:center;
            font-size:38px;
            font-weight:900;
            color:#4B2ECF;
            margin-bottom:20px;
        }}
        .pass-card {{
            width:550px;
            margin:0 auto;
            background:white;
            padding:30px;
            border-radius:15px;
            box-shadow:0 6px 18px rgba(0,0,0,0.15);
            text-align:center;
        }}
        .visitor-img {{
            width:150px;
            height:150px;
            border-radius:10px;
            border:3px solid #4B2ECF;
            margin-bottom:12px;
        }}
        .data-text {{
            text-align:left;
            margin-top:8px;
            font-size:18px;
        }}
        .action-btn button {{
            background:{HEADER_GRADIENT} !important;
            color:white !important;
            border:none !important;
            border-radius:8px !important;
            padding:12px !important;
            font-size:18px !important;
            margin-bottom:15px !important;
            width:240px !important;
        }}
    </style>
    """, unsafe_allow_html=True)


# ======================================================
# PASS UI
# ======================================================
def show_pass(visitor, photo_bytes):
    base64_img = base64.b64encode(photo_bytes).decode()

    load_styles()
    st.markdown("<div class='title'>Visitor Pass</div>", unsafe_allow_html=True)
    st.markdown("<div class='pass-card'>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="text-align:center;">
            <img src="data:image/jpeg;base64,{base64_img}" class="visitor-img"/>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="data-text">
            <p><strong>Name:</strong> {visitor['full_name']}</p>
            <p><strong>Company:</strong> {visitor['from_company']}</p>
            <p><strong>To Meet:</strong> {visitor['person_to_meet']}</p>
            <p><strong>Visitor ID:</strong> #{visitor['visitor_id']}</p>
            <p><strong>Date:</strong> {visitor['registration_timestamp'].strftime('%d-%m-%Y %H:%M')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.write("")

    st.markdown("<div class='action-btn'>", unsafe_allow_html=True)

    if st.button("New Visitor"):
        st.session_state.pop("current_visitor_id", None)
        st.session_state["current_page"] = "visitor_details"
        st.session_state["show_pass"] = False
        st.rerun()

    if st.button("Dashboard"):
        st.session_state["show_pass"] = False
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    if st.button("Logout"):
        st.session_state.clear()
        st.session_state["current_page"] = "visitor_login"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ======================================================
# MAIN
# ======================================================
def render_identity_page():
    if not st.session_state.get("admin_logged_in", False):
        st.session_state["current_page"] = "visitor_login"
        st.rerun()

    # If pass generated → show the pass
    if st.session_state.get("show_pass", False):
        visitor = get_visitor_data(st.session_state["current_visitor_id"])
        show_pass(visitor, st.session_state["pass_photo"])
        return

    # else show camera page
    visitor = get_visitor_data(st.session_state["current_visitor_id"])

    st.title("Capture Visitor Photo")

    camera_photo = st.camera_input("Take a Photo")

    if st.button("Save & Generate Pass"):
        if not camera_photo:
            st.error("Please take a photo first")
            return

        photo_bytes = camera_photo.getvalue()

        save_photo(visitor["visitor_id"], visitor["full_name"], visitor["from_company"], photo_bytes)

        st.session_state["pass_photo"] = photo_bytes
        st.session_state["show_pass"] = True
        st.rerun()

    if st.button("Back"):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()
