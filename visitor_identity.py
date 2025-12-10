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

    # Download Excel
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

    img = PILImage.open(io.BytesIO(photo_bytes))
    img.thumbnail((120, 120))
    photo = XLImage(img)
    photo.anchor = f"C{next_row}"
    ws.add_image(photo)

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


# ---------------- Visitor Pass Card ----------------
def render_pass(visitor, photo_bytes):
    # Photo Base64 for HTML
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


# ---------------- Main Page ----------------
def render_identity_page():
    if "current_visitor_id" not in st.session_state:
        st.error("No visitor selected.")
        return

    visitor_id = st.session_state["current_visitor_id"]
    visitor = get_visitor_info(visitor_id)

    st.title("🆔 Visitor Identity Capture")

    st.subheader(f"Visitor: {visitor['full_name']}")
    st.markdown(f"**Company:** {visitor['from_company']}")

    st.write("### Capture Photo")
    camera_photo = st.camera_input("Take photo for visitor pass")

    if st.button("Save & Generate Pass →"):
        if not camera_photo:
            st.error("Please capture a photo.")
            return

        photo_bytes = camera_photo.read()

        with st.spinner("Updating Excel & generating pass..."):
            updated = update_excel_with_photo(
                visitor["full_name"], visitor["from_company"], photo_bytes
            )

        if updated:
            st.success("Visitor identity saved successfully!")

            # Render digital pass
            render_pass(visitor, photo_bytes)

            st.markdown("### Actions")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("➕ New Visitor"):
                    st.session_state.pop("visitor_data", None)
                    st.session_state.pop("current_visitor_id", None)
                    st.session_state["registration_step"] = "primary"
                    st.session_state["current_page"] = "visitor_details"
                    st.rerun()

            with col2:
                if st.button("🚪 Logout"):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.session_state["current_page"] = "visitor_login"
                    st.rerun()

            with col3:
                if st.button("Dashboard →"):
                    st.session_state["current_page"] = "visitor_dashboard"
                    st.rerun()

        else:
            st.error("Could not update Excel")

    st.write("")
    if st.button("← Back"):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()


def render_identity():
    return render_identity_page()
