import streamlit as st
import boto3
import json
import mysql.connector
import pandas as pd
from datetime import datetime, date


# =====================================================
# CONFIG
# =====================================================
AWS_REGION = "ap-south-1"
AWS_SECRET = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"


# =====================================================
# SECRETS MANAGER
# =====================================================
@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    response = client.get_secret_value(SecretId=AWS_SECRET)
    return json.loads(response["SecretString"])


def get_conn():
    creds = get_credentials()
    return mysql.connector.connect(
        host=creds["DB_HOST"],
        user=creds["DB_USER"],
        password=creds["DB_PASSWORD"],
        database=creds["DB_NAME"],
        autocommit=True
    )


# =====================================================
# DB QUERY – TODAY’S VISITORS
# =====================================================
def get_today_visitors(company_id: int):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT visitor_id,
               full_name,
               phone_number,
               person_to_meet,
               registration_timestamp,
               checkout_time,
               pass_generated
        FROM visitors
        WHERE company_id=%s
          AND DATE(registration_timestamp)=CURDATE()
          AND pass_generated=1
        ORDER BY registration_timestamp DESC;
    """, (company_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# =====================================================
# CHECKOUT ACTION
# =====================================================
def checkout_visitor(visitor_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE visitors SET checkout_time=NOW() WHERE visitor_id=%s",
        (visitor_id,)
    )
    cur.close()
    conn.close()


# =====================================================
# UI CSS
# =====================================================
def inject_css():
    st.markdown("""
    <style>
        .summary-card {
            background:white;
            padding:18px 22px;
            border-radius:14px;
            box-shadow:0 3px 12px rgba(0,0,0,0.08);
            margin-bottom:14px;
        }
        .summary-title {
            font-size:14px;
            opacity:0.7;
        }
        .summary-value {
            font-size:26px;
            font-weight:800;
            color:#50309D;
        }
        .visitor-table-header {
            font-size:28px;
            font-weight:800;
            margin-bottom:14px;
            margin-top:10px;
        }
        .new-btn {
            display:inline-block;
            padding:10px 18px;
            border-radius:8px;
            border:1px solid #50309D;
            color:#50309D;
            font-weight:600;
        }
        .summary-title-row {
            display:flex;
            align-items:center;
            gap:8px;
            font-size:22px;
            font-weight:700;
            margin-bottom:14px;
        }
    </style>
    """, unsafe_allow_html=True)


# =====================================================
# MAIN PAGE
# =====================================================
def render_visitor_dashboard():

    inject_css()

    # ---------------- AUTH ----------------
    company_id = st.session_state.get("company_id")
    if not company_id:
        st.error("Unauthorized. Login again.")
        st.stop()

    # ---------------- DATA ----------------
    visitors = get_today_visitors(company_id)

    total_visitors = len(visitors)
    currently_inside = sum(1 for v in visitors if v["checkout_time"] is None)
    checked_out_today = sum(1 for v in visitors if v["checkout_time"] is not None)

    # ---------------- HEADER ----------------
    st.markdown(
        f"""
        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-bottom:20px;
        ">
            <a class="new-btn" href="#" onclick="window.location.reload()">NEW VISITOR REGISTRATION</a>
            <img src="{LOGO_URL}" height="55">
        </div>
        """, unsafe_allow_html=True
    )

    # ---------------- BODY LAYOUT ----------------
    col_left, col_right = st.columns([2.2, 0.8])

    # ---------------- LEFT : TABLE ----------------
    with col_left:

        st.markdown('<div class="visitor-table-header">Visitor List</div>', unsafe_allow_html=True)

        if not visitors:
            st.info("No visitors today.")
        else:
            df = pd.DataFrame(visitors)

            df["Visited"] = (
                pd.to_datetime(df["registration_timestamp"])
                  .dt.strftime("%d-%m-%Y %H:%M")
            )
            df["Checkout"] = df["checkout_time"].apply(
                lambda x: "-" if x is None else pd.to_datetime(x).strftime("%H:%M")
            )

            df_display = df[["full_name", "phone_number", "person_to_meet", "Visited", "Checkout"]]
            df_display.columns = ["Name", "Phone", "Meeting", "Visited", "Checkout"]

            st.table(df_display)

            # --------- Checkout Buttons ---------
            for idx, row in df.iterrows():
                if row["checkout_time"] is None:
                    if st.button("Checkout", key=f"chk_{row['visitor_id']}"):
                        checkout_visitor(row["visitor_id"])
                        st.rerun()

    # ---------------- RIGHT : SUMMARY ----------------
    with col_right:
        st.markdown(
            '<div class="summary-title-row">📊 Summary</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="summary-card">
                <div class="summary-title">Visitors Today</div>
                <div class="summary-value">{total_visitors}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="summary-card">
                <div class="summary-title">Currently Inside</div>
                <div class="summary-value">{currently_inside}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="summary-card">
                <div class="summary-title">Checked Out Today</div>
                <div class="summary-value">{checked_out_today}</div>
            </div>
            """,
            unsafe_allow_html=True
        )


# =====================================================
# PAGE ROUTE
# =====================================================
if "company_id" not in st.session_state:
    # example to test UI
    st.session_state["company_id"] = 1

render_visitor_dashboard()
