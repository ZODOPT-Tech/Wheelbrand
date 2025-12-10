import streamlit as st
from datetime import datetime
import boto3
import base64
import io
import json
import mysql.connector
from PIL import Image as PILImage
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XLImage


# ==============================
# AWS + DB CONFIG
# ==============================
AWS_REGION = "ap-south-1"
AWS_BUCKET = "zodoptvisiorsmanagement"
EXCEL_KEY = "visitorsphoto.xlsx"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"


# ==============================
# DB CREDENTIALS (AWS)
# ==============================
@st.cache_resource
def get_db_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    secret = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(secret["SecretString"])


# ==============================
# DB CONNECTION
# ==============================
@st.cache_resource
def get_connection():
    creds = get_db_credentials()
    return mysql.connector.connect(
        host=creds["DB_HOST"],
        user=creds["DB_USER"],
        password=creds["DB_PASSWORD"],
        database=creds["DB_NAME"],
        autocommit=True
    )


# ==============================
# FETCH VISITOR
# ==============================
def get_visitor_info(visitor_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT visitor_id, full_name, from_company
        FROM visitors
        WHERE visitor_id = %s
    """, (visitor_id,))
    
    visitor = cursor.fetchone()
    cursor.close()
    return visitor


# ==============================
# SAVE PHOTO INTO S3 EXCEL
# ==============================
def update_excel_with_photo(visitor_name, company_name, photo_bytes):
    s3 = boto3.client("s3")

    # Download existing Excel
    obj = s3.get_object(Bucket=AWS_BUCKET, Key=EXCEL_KEY)
    wb = load_workbook(io.BytesIO(obj["Body"].read()))
    ws = wb.active

    # Row insert
    row = ws.max_row + 1
    ws[f"A{row}"] = visitor_name
    ws[f"B{row}"] = company_name
    ws[f"D{row}"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Photo insert
    img = PILImage.open(io.BytesIO(photo_bytes))
    img.thumbnail((120, 120))
    xl_img = XLImage(img)
    xl_img.anchor = f"C{row}"
    ws.add_image(xl_img)

    # Save to buffer
    out = io.BytesIO()
    wb.save(out)
    out.seek(0)

    # Upload updated Excel
    s3.put_object(
        Bucket=AWS_BUCKET,
        Key=EXCEL_KEY,
        Body=out.getvalue(),
        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    return True


# ==============================
# PASS GENERATION UI
# ==============================
def render_pass(visitor, photo_bytes):
    base64_photo = base64.b64encode(photo_bytes).decode()

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
            <h2 style="text-align:center;color:#5036FF;">VISITOR PASS</h2>
            <div style="text-align:center;">
                <img src="data:image/jpeg;base64,{base64_photo}"
                    style="width:120px;height:120px;border-radius:10px;border:2px solid #5036FF;">
            </div>
            <hr/>
            <p><b>Name:</b> {visitor['full_name']}</p>
            <p><b>Company:</b> {visitor['from_company']}</p>
            <p><b>Visitor ID:</b> #{visitor['visitor_id']}</p>
            <p><b>Date:</b> {datetime.now().strftime("%d-%m-%Y %H:%M")}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# ==============================
# ENTRY POINT
# ==============================
def render_identity_page():
    """
    This function is called from main.py using:
    PAGE_MODULES['visitor_identity']
    """
    
    # Access Check
    if not st.session_state.get("admin_logged_in", False):
        st.warning("Unauthorized, please login.")
        st.session_state["current_page"] = "visitor_login"
        st.rerun()

    # Check visitor selection
    if "current_visitor_id" not in st.session_state:
        st.error("No visitor selected.")
        st.session_state["current_page"] = "visitor_details"
        st.rerun()

    visitor_id = st.session_state["current_visitor_id"]
    visitor = get_visitor_info(visitor_id)

    st.title("🆔 Capture Identity & Generate Visitor Pass")
    st.subheader(visitor["full_name"])
    st.markdown(f"**Company:** {visitor['from_company']}")

    camera_photo = st.camera_input("Capture Visitor Photo")

    if st.button("💾 Save & Generate Pass"):
        if not camera_photo:
            st.error("Please capture a photo first.")
            return
        
        photo_bytes = camera_photo.read()

        with st.spinner("Updating records..."):
            ok = update_excel_with_photo(visitor["full_name"], visitor["from_company"], photo_bytes)
        
        if ok:
            st.success("Visitor identity saved successfully!")
            render_pass(visitor, photo_bytes)

            st.markdown("### Actions")
            c1, c2, c3 = st.columns(3)

            with c1:
                if st.button("➕ New Visitor"):
                    st.session_state["visitor_data"] = {}
                    st.session_state["registration_step"] = "primary"
                    st.session_state.pop("current_visitor_id", None)
                    st.session_state["current_page"] = "visitor_details"
                    st.rerun()

            with c2:
                if st.button("📊 Dashboard"):
                    st.session_state["current_page"] = "visitor_dashboard"
                    st.rerun()

            with c3:
                if st.button("🚪 Logout"):
                    st.session_state.clear()
                    st.session_state["current_page"] = "visitor_login"
                    st.rerun()
        else:
            st.error("Failed to update Excel.")

    if st.button("← Back"):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()
