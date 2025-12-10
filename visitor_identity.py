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


# ---------------- Fetch Visitor Info for Excel ----------------
def get_visitor_info(visitor_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT full_name, from_company
        FROM visitors
        WHERE visitor_id=%s
        """,
        (visitor_id,),
    )
    return cursor.fetchone()


# ---------------- Excel Update Logic ----------------
def update_excel_with_photo(visitor_name, company_name, photo_bytes):
    s3 = boto3.client("s3")

    # Step 1: Download the existing Excel file
    try:
        obj = s3.get_object(Bucket=AWS_BUCKET, Key=EXCEL_KEY)
        data = obj["Body"].read()
    except Exception:
        st.error("Excel file not found in S3. Please upload visitorsphoto.xlsx first.")
        return False

    # Step 2: Load workbook
    wb = load_workbook(io.BytesIO(data))
    ws = wb.active

    # Step 3: Find next row
    next_row = ws.max_row + 1

    # Step 4: Add text columns
    ws[f"A{next_row}"] = visitor_name
    ws[f"B{next_row}"] = company_name
    ws[f"D{next_row}"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Step 5: Insert image
    img = PILImage.open(io.BytesIO(photo_bytes))
    img.thumbnail((120, 120))
    photo = XLImage(img)

    photo.anchor = f"C{next_row}"
    ws.add_image(photo)

    # Step 6: Save workbook to memory
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    # Step 7: Upload back to S3
    s3.put_object(
        Bucket=AWS_BUCKET,
        Key=EXCEL_KEY,
        Body=output.getvalue(),
        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    return True


# ---------------- UI ----------------
def render_identity_page():
    if "current_visitor_id" not in st.session_state:
        st.error("No visitor selected.")
        return

    visitor_id = st.session_state["current_visitor_id"]
    info = get_visitor_info(visitor_id)

    st.title("🆔 Visitor Identity Capture")

    st.subheader(f"Visitor: {info['full_name']}")
    st.markdown(f"**Company:** {info['from_company']}")

    st.write("")
    st.write("### Capture Photo")
    camera_photo = st.camera_input("Take photo for identity record")

    st.write("")
    if st.button("Save Identity →"):
        if not camera_photo:
            st.error("Please capture a photo.")
            return

        photo_bytes = camera_photo.read()

        with st.spinner("Updating Excel..."):
            status = update_excel_with_photo(
                info["full_name"],
                info["from_company"],
                photo_bytes
            )

        if status:
            st.success("Visitor identity saved successfully!")
            st.balloons()
            st.session_state["current_page"] = "visitor_dashboard"
            st.rerun()
        else:
            st.error("Failed to update Excel")


    if st.button("← Back to Dashboard"):
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()


def render_identity():
    return render_identity_page()
