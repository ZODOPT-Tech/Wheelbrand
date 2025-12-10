import streamlit as st
from datetime import datetime
import boto3
import base64
import io
import mysql.connector
import json
from PIL import Image as PILImage
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XLImage


AWS_REGION = "ap-south-1"
AWS_BUCKET = "zodoptvisiorsmanagement"
EXCEL_KEY = "visitorsphoto.xlsx"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"


# ---------------- AWS Secret ----------------
@st.cache_resource
def get_db_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    secret = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(secret["SecretString"])


@st.cache_resource
def get_connection():
    creds = get_db_credentials()
    return mysql.connector.connect(
        host=creds["DB_HOST"],
        user=creds["DB_USER"],
        password=creds["DB_PASSWORD"],
        database=creds["DB_NAME"],
        autocommit=True,
    )


# ---------------- Fetch Visitor Info ----------------
def get_visitor_info(visitor_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT visitor_id, full_name, from_company
        FROM visitors
        WHERE visitor_id=%s
        """,
        (visitor_id,),
    )
    return cursor.fetchone()


# ---------------- Excel Update Logic ----------------
def update_excel_with_photo(visitor_name, company_name, photo_bytes):
    s3 = boto3.client("s3")

    # Step 1: Download Excel
    try:
        obj = s3.get_object(Bucket=AWS_BUCKET, Key=EXCEL_KEY)
        data = obj["Body"].read()
    except Exception:
        return False

    wb = load_workbook(io.BytesIO(data))
    ws = wb.active

    next_row = ws.max_row + 1

    ws[f"A{next_row}"] = visitor_name
    ws[f"B{next_row}"] = company_name
    ws[f"D{next_row}"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Insert Photo
    img = PILImage.open(io.BytesIO(photo_bytes))
    img.thumbnail((120, 120))
    photo = XLImage(img)
    photo.anchor = f"C{next_row}"
    ws.add_image(photo)

    # Save and Upload back
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    s3.put_object(
        Bucket=AWS_BUCKET,
        Key=EXCEL_KEY,
        Body=output.getvalue(),
        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    return True


# ---------------- Digital Visitor Pass ----------------
def render_pass(visitor, photo_bytes):
    base64_img = base64.b64encode(photo_bytes).decode()

    st.markdown(
        f"""
        <div style="
            width:400px;
            border-radius:16px;
            padding:20px;
            background:white;
            box-shadow:0 4px 12px rgba(0,0,0,0.15);
            margin-bottom:25px;
        ">
            <h2 style="text-align:center;color:#5036FF;margin-bottom:10px;">VISITOR PASS</h2>
            <div style="text-align:center;">
                <img src="data:image/jpeg;base64,{base64_img}"
                    style="width:120px;height:120px;border-radius:10px;border:2px solid #5036FF;"/>
            </div>

            <hr style="margin:15px 0;"/>

            <p><b>Name:</b> {visitor["full_name"]}</p>
            <p><b>Company:</b> {visitor["from_company"]}</p>
            <p><b>Visitor ID:</b> #{visitor["visitor_id"]}</p>
            <p><b>Date:</b> {datetime.now().strftime("%d-%m-%Y %H:%M")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------- Identity Page ----------------
def render_identity_page():
    # Authentication check
    if not st.session_state.get("admin_logged_in", False):
        st.warning("Unauthorized access")
        st.session_state["current_page"] = "visitor_login"
        st.rerun()

    # Visitor flow check
    if "current_visitor_id" not in st.session_state:
        st.error("No visitor selected.")
        st.session_state["current_page"] = "visitor_details"
        st.rerun()

    visitor_id = st.session_state["current_visitor_id"]
    visitor = get_visitor_info(visitor_id)

    st.title("🆔 Identity Capture & Visitor Pass")
    st.subheader(f"Visitor: {visitor['full_name']}")
    st.markdown(f"**Company:** {visitor['from_company']}")

    camera_photo = st.camera_input("Capture Visitor Photo")

    if st.button("Save & Generate Visitor Pass →"):
        if not camera_photo:
            st.error("Please capture a photo first.")
            return

        photo_bytes = camera_photo.read()

        with st.spinner("Saving photo & updating visitor pass..."):
            updated = update_excel_with_photo(
                visitor["full_name"],
                visitor["from_company"],
                photo_bytes
            )

        if updated:
            st.success("Visitor identity saved!")
            render_pass(visitor, photo_bytes)

            st.markdown("### Actions")

            col1, col2, col3 = st.columns(3)

            # NEW VISITOR
            with col1:
                if st.button("➕ New Visitor"):
                    st.session_state["visitor_data"] = {}
                    st.session_state["registration_step"] = "primary"
                    st.session_state.pop("current_visitor_id", None)
                    st.session_state["current_page"] = "visitor_details"
                    st.rerun()

            # LOGOUT
            with col2:
                if st.button("🚪 Logout"):
                    st.session_state.clear()
                    st.session_state["current_page"] = "visitor_login"
                    st.rerun()

            # DASHBOARD
            with col3:
                if st.button("📊 Dashboard"):
                    st.session_state["current_page"] = "visitor_dashboard"
                    st.rerun()

        else:
            st.error("Failed to update Excel file.")

    st.write("")
    if st.button("← Back"):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()
