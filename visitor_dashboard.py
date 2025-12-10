import streamlit as st
import mysql.connector
from datetime import datetime
import boto3
import json


# ====================================================
# CONFIG
# ====================================================
AWS_REGION = "ap-south-1"
AWS_SECRET = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #4B2ECF, #7A42FF)"


# ====================================================
# SECRETS + DB
# ====================================================
@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    raw = client.get_secret_value(SecretId=AWS_SECRET)
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


# ====================================================
# CSS
# ====================================================
def inject_css():
    st.markdown(f"""
    <style>

    header[data-testid="stHeader"] {{
        display: none;
    }}

    .block-container {{
        padding-top: 0;
    }}

    .header-box {{
        background: {HEADER_GRADIENT};
        padding: 24px 40px;
        border-radius: 14px;
        margin-bottom: 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    }}

    .head-title {{
        font-size: 32px;
        font-weight: 900;
        color: white;
    }}

    .summary-card {{
        background: white;
        padding: 16px 22px;
        border-radius: 14px;
        box-shadow: 0 3px 12px rgba(0,0,0,0.1);
        margin-bottom: 16px;
    }}

    .summary-title {{
        font-size: 14px;
        opacity: 0.7;
    }}

    .summary-value {{
        font-size: 26px;
        font-weight: 800;
        color: #4B2ECF;
    }}

    .new-btn button {{
        background: {HEADER_GRADIENT} !important;
        color: white !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        width: 100%;
        padding: 14px 0px !important;
        border: none !important;
    }}

    .done-tag {{
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 13px;
        background: #28a745;
        color: white;
        font-weight: 600;
        text-align: center;
        display: inline-block;
    }}

    </style>
    """, unsafe_allow_html=True)


# ====================================================
# FETCH DATA
# ====================================================
def get_visitors(company_id):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT visitor_id, full_name, phone_number, person_to_meet,
               registration_timestamp, checkout_time
        FROM visitors
        WHERE company_id=%s
          AND pass_generated=1
          AND DATE(registration_timestamp)=CURDATE()
        ORDER BY registration_timestamp DESC
    """, (company_id,))
    return cur.fetchall()


def get_summary(company_id):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    # total visitors today
    cur.execute("""
        SELECT COUNT(*) AS c
        FROM visitors
        WHERE company_id=%s
          AND pass_generated=1
          AND DATE(registration_timestamp)=CURDATE()
    """, (company_id,))
    total = cur.fetchone()['c']

    # currently inside
    cur.execute("""
        SELECT COUNT(*) AS c
        FROM visitors
        WHERE company_id=%s
          AND pass_generated=1
          AND checkout_time IS NULL
          AND DATE(registration_timestamp)=CURDATE()
    """, (company_id,))
    inside = cur.fetchone()['c']

    # checked out today
    cur.execute("""
        SELECT COUNT(*) AS c
        FROM visitors
        WHERE company_id=%s
          AND pass_generated=1
          AND DATE(checkout_time)=CURDATE()
    """, (company_id,))
    out = cur.fetchone()['c']

    return total, inside, out


def checkout(visitor_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE visitors
        SET checkout_time=%s
        WHERE visitor_id=%s
    """, (datetime.now(), visitor_id))


# ====================================================
# DASHBOARD UI
# ====================================================
def render_dashboard():

    if not st.session_state.get("admin_logged_in"):
        st.error("Unauthorized. Please login.")
        st.stop()

    inject_css()

    company_name = st.session_state.get("company_name", "Your Company")
    company_id = st.session_state.get("company_id")

    # ------------------------------------------------
    # Header
    # ------------------------------------------------
    st.markdown(f"""
        <div class="header-box">
            <div class="head-title">Welcome, {company_name}</div>
            <img src="{LOGO_URL}" height="55px">
        </div>
    """, unsafe_allow_html=True)


    left, right = st.columns([4, 1.5])

    # ------------------------------------------------
    # SUMMARY SECTION
    # ------------------------------------------------
    with right:
        st.markdown("### 📊 Summary")
        total, inside, out = get_summary(company_id)

        for title, val in [
            ("Visitors Today", total),
            ("Currently Inside", inside),
            ("Checked Out Today", out)
        ]:
            st.markdown(f"""
                <div class="summary-card">
                    <div class="summary-title">{title}</div>
                    <div class="summary-value">{val}</div>
                </div>
            """, unsafe_allow_html=True)


    # ------------------------------------------------
    # VISITOR TABLE + NEW REGISTRATION
    # ------------------------------------------------
    with left:

        # --- Reset visitor session before new registration ---
        st.markdown("<div class='new-btn'>", unsafe_allow_html=True)
        if st.button("NEW VISITOR REGISTRATION"):

            # Clear previous visitor session info
            for key in ["current_visitor_id", "pass_data", "pass_image",
                        "visitor_photo_bytes", "email_sent"]:
                if key in st.session_state:
                    del st.session_state[key]

            # Start at PRIMARY page
            st.session_state["current_page"] = "visitor_details_primary"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("## Visitor List")

        rows = get_visitors(company_id)

        if not rows:
            st.info("No visitors today.")
            return

        # table header
        h = st.columns([3, 2, 2, 3, 2, 2])
        h[0].markdown("**Name**")
        h[1].markdown("**Phone**")
        h[2].markdown("**Meeting**")
        h[3].markdown("**Visited**")
        h[4].markdown("**Checkout**")
        h[5].markdown("**Action**")

        st.markdown("---")

        # table rows
        for v in rows:
            vid = v["visitor_id"]
            visited = v["registration_timestamp"].strftime("%d-%m-%Y %H:%M")
            checkout_time = v["checkout_time"].strftime("%d-%m-%Y %H:%M") if v["checkout_time"] else "—"

            r = st.columns([3, 2, 2, 3, 2, 2])
            r[0].write(v["full_name"])
            r[1].write(v["phone_number"])
            r[2].write(v["person_to_meet"])
            r[3].write(visited)
            r[4].write(checkout_time)

            with r[5]:
                if not v["checkout_time"]:
                    if st.button("Checkout", key=f"checkout_{vid}"):
                        checkout(vid)
                        st.rerun()
                else:
                    st.markdown("<div class='done-tag'>Done</div>", unsafe_allow_html=True)
