import streamlit as st
import mysql.connector
import json
import boto3
from datetime import datetime


# ======================================================
# CONFIG
# ======================================================
AWS_REGION = "ap-south-1"
AWS_SECRET_ARN = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
HEADER_GRADIENT = "linear-gradient(90deg, #4B2ECF, #7A42FF)"
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"


# ======================================================
# AWS CREDENTIALS
# ======================================================
@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    raw = client.get_secret_value(SecretId=AWS_SECRET_ARN)
    return json.loads(raw["SecretString"])


@st.cache_resource
def get_conn():
    c = get_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True
    )


# ======================================================
# CSS
# ======================================================
def load_css():
    st.markdown(f"""
    <style>
    .stApp > header {{visibility: hidden;}}

    .header-box {{
        background: {HEADER_GRADIENT};
        padding: 26px 45px;
        border-radius: 12px;
        margin-bottom: 35px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0px 4px 22px rgba(0,0,0,0.25);
    }}
    .header-title {{
        font-size: 38px;
        font-weight: 800;
        color: white;
        margin: 0;
    }}
    .header-logo {{
        height: 55px;
    }}

    .summary-card {{
        background: white;
        padding: 18px 20px;
        border-radius: 12px;
        margin-bottom: 18px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
    }}
    .summary-title {{
        font-size: 15px;
        font-weight: 600;
        color: #666;
    }}
    .summary-value {{
        font-size: 28px;
        font-weight: 800;
        color: #4B2ECF;
    }}

    .new-btn button {{
        background: {HEADER_GRADIENT} !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 16px !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        width: 100% !important;
    }}

    .checkout-btn button {{
        background: {HEADER_GRADIENT} !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 8px 14px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
    }}

    .completed {{
        background: #28a745;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 13px;
        color: white;
        font-weight: 600;
        text-align: center;
        display: inline-block;
    }}
    </style>
    """, unsafe_allow_html=True)


# ======================================================
# HEADER
# ======================================================
def render_header():
    company_name = st.session_state.get("company_name", "Visitor Dashboard")
    st.markdown(f"""
        <div class="header-box">
            <div class="header-title">Welcome, {company_name}</div>
            <img src="{LOGO_URL}" class="header-logo">
        </div>
    """, unsafe_allow_html=True)


# ======================================================
# FETCH VISITORS
# ======================================================
def get_visitors_today(company_id):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT visitor_id,
               full_name,
               phone_number,
               person_to_meet,
               registration_timestamp,
               checkout_time
        FROM visitors
        WHERE company_id=%s
          AND status='approved'
          AND pass_generated=1
          AND DATE(registration_timestamp)=CURDATE()
        ORDER BY registration_timestamp DESC;
    """, (company_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def checkout(visitor_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE visitors SET checkout_time=NOW() WHERE visitor_id=%s",
        (visitor_id,)
    )
    conn.commit()
    cur.close()
    conn.close()


# ======================================================
# STATS
# ======================================================
def compute_stats(visitors):
    total = len(visitors)
    inside = sum(1 for v in visitors if v["checkout_time"] is None)
    out = total - inside
    return total, inside, out


# ======================================================
# MAIN UI
# ======================================================
def render_visitor_dashboard():

    if not st.session_state.get("admin_logged_in"):
        st.error("Access Denied")
        st.stop()

    load_css()
    render_header()

    company_id = st.session_state["company_id"]
    visitors = get_visitors_today(company_id)

    total, inside, out = compute_stats(visitors)

    left, right = st.columns([4, 1.4])

    with right:
        st.markdown("### 📊 Summary")
        for title, val in [
            ("Visitors Today", total),
            ("Currently Inside", inside),
            ("Checked Out Today", out)
        ]:
            st.markdown(
                f"""
                <div class="summary-card">
                    <div class="summary-title">{title}</div>
                    <div class="summary-value">{val}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    with left:
        st.markdown("<div class='new-btn'>", unsafe_allow_html=True)
        if st.button("NEW VISITOR REGISTRATION"):
            st.session_state["current_page"] = "visitor_details"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("## Visitor List")

        if not visitors:
            st.info("No approved visitors today.")
            return

        header = st.columns([3, 2, 2, 3, 2, 2])
        header[0].markdown("### Name")
        header[1].markdown("### Phone")
        header[2].markdown("### Meeting")
        header[3].markdown("### Visited")
        header[4].markdown("### Checkout")
        header[5].markdown("### Action")

        st.markdown("---")

        for v in visitors:
            vid = v["visitor_id"]
            checkout_text = v["checkout_time"].strftime("%d-%m-%Y %H:%M") if v["checkout_time"] else "—"

            row = st.columns([3, 2, 2, 3, 2, 2])
            row[0].write(v["full_name"])
            row[1].write(v["phone_number"])
            row[2].write(v["person_to_meet"])
            row[3].write(v["registration_timestamp"].strftime("%d-%m-%Y %H:%M"))
            row[4].write(checkout_text)

            with row[5]:
                if v["checkout_time"]:
                    st.markdown("<div class='completed'>Completed</div>", unsafe_allow_html=True)
                else:
                    if st.button("Checkout", key=f"co_{vid}"):
                        checkout(vid)
                        st.rerun()


# Export router entry
def render_dashboard():
    return render_visitor_dashboard()
