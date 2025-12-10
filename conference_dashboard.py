import streamlit as st
import boto3
import json
import mysql.connector
import pandas as pd
from datetime import datetime


# =====================================================
# CONFIG
# =====================================================
AWS_REGION = "ap-south-1"
AWS_SECRET = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


# =====================================================
# SECRETS
# =====================================================
@st.cache_resource
def get_credentials():
    """AWS Secrets Manager credentials cache."""
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    result = client.get_secret_value(SecretId=AWS_SECRET)
    return json.loads(result["SecretString"])


def get_conn():
    """ALWAYS return a fresh DB connection (live data)."""
    c = get_credentials()
    return mysql.connector.connect(
        host=c["DB_HOST"],
        user=c["DB_USER"],
        password=c["DB_PASSWORD"],
        database=c["DB_NAME"],
        autocommit=True
    )


# =====================================================
# DB QUERIES
# =====================================================
def get_company_user(user_id: int):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT name, company FROM conference_users WHERE id=%s LIMIT 1",
        (user_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_company_bookings(company: str):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT b.id,
               u.name AS booked_by,
               u.department,
               b.start_time,
               b.end_time,
               b.purpose
        FROM conference_bookings b
        JOIN conference_users u ON u.id=b.user_id
        WHERE u.company=%s
        ORDER BY b.start_time DESC;
    """, (company,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_today_visitors(company: str):
    """Visitors whose pass is generated today."""
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT v.full_name,
               v.from_company,
               v.person_to_meet,
               vi.created_at AS pass_time
        FROM visitors v
        JOIN visitor_identity vi ON vi.visitor_id=v.visitor_id
        WHERE v.company=%s
          AND DATE(vi.created_at)=CURDATE()
          AND v.pass_generated=1
        ORDER BY vi.created_at DESC;
    """, (company,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# =====================================================
# CUSTOM CSS
# =====================================================
def inject_css():
    st.markdown(f"""
    <style>
    header[data-testid="stHeader"] {{display:none;}}
    .block-container {{padding-top:0;}}

    .header-box {{
        background:{GRADIENT};
        margin:-1rem -1rem 1.5rem -1rem;
        border-radius:20px;
        padding:28px 40px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 6px 20px rgba(0,0,0,0.18);
    }}
    .welcome {{
        font-size:32px;
        font-weight:900;
        color:white;
        margin-bottom:5px;
    }}
    .company {{
        font-size:20px;
        font-weight:600;
        color:white;
        opacity:0.9;
    }}
    .header-logo {{
        height:60px;
    }}

    .summary-card {{
        background:white;
        padding:16px 22px;
        border-radius:14px;
        box-shadow:0 3px 12px rgba(0,0,0,0.1);
        margin-bottom:16px;
    }}
    .summary-title {{
        font-size:14px;
        opacity:0.7;
    }}
    .summary-value {{
        font-size:26px;
        font-weight:800;
        color:#50309D;
    }}
    </style>
    """, unsafe_allow_html=True)


# =====================================================
# MAIN DASHBOARD
# =====================================================
def render_dashboard():
    inject_css()

    # ------------------ AUTH CHECK ------------------
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("Unauthorized. Login again.")
        st.stop()

    user = get_company_user(user_id)
    company = user["company"]

    # ------------------ FETCH DATA ------------------
    all_bookings = get_company_bookings(company)
    visitors_today = get_today_visitors(company)

    today = datetime.today().date()
    todays_bookings = [
        b for b in all_bookings if b["start_time"].date() == today
    ]

    # ------------------ GROUP BY DEPARTMENT ------------------
    dept_count = {}
    for b in todays_bookings:
        dept = b["department"]
        dept_count[dept] = dept_count.get(dept, 0) + 1

    # ------------------ HEADER ------------------
    st.markdown(
        f"""
        <div class="header-box">
            <div>
                <div class="welcome">Welcome</div>
                <div class="company">{company}</div>
            </div>
            <img class="header-logo" src="{LOGO_URL}">
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------ ACTION BUTTONS ------------------
    left_action, right_action = st.columns(2)

    with left_action:
        if st.button("New Booking", use_container_width=True):
            st.session_state["current_page"] = "conference_bookings"
            st.rerun()

    with right_action:
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.session_state["current_page"] = "conference_login"
            st.rerun()

    st.write("")

    # ==================================================
    # SUMMARY CARDS BELOW BUTTONS
    # ==================================================
    st.subheader("Summary (Today)")
    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.markdown(
            f"""
            <div class="summary-card">
                <div class="summary-title">Today's Bookings</div>
                <div class="summary-value">{len(todays_bookings)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_s2:
        st.markdown(
            f"""
            <div class="summary-card">
                <div class="summary-title">Visitors Arrived</div>
                <div class="summary-value">{len(visitors_today)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # ------------------ BODY LAYOUT ------------------
    col_left, col_right = st.columns([2, 1])

    # ------------------ TABLE LEFT ------------------
    with col_left:
        # BOOKING TABLE
        st.subheader("Today's Booking List")

        if not todays_bookings:
            st.info("No bookings today.")
        else:
            df = pd.DataFrame(todays_bookings)
            df["Date"] = pd.to_datetime(df["start_time"]).dt.date
            df["Time"] = (
                pd.to_datetime(df["start_time"]).dt.strftime("%I:%M %p")
                + " - "
                + pd.to_datetime(df["end_time"]).dt.strftime("%I:%M %p")
            )

            df = df[["booked_by", "department", "Date", "Time", "purpose"]]
            df.index = df.index + 1

            st.dataframe(df, use_container_width=True, height=350)

        # VISITOR TABLE
        st.subheader("Today's Visitors")

        if not visitors_today:
            st.info("No visitors arrived yet.")
        else:
            dfv = pd.DataFrame(visitors_today)
            dfv["Time"] = pd.to_datetime(dfv["pass_time"]).dt.strftime("%I:%M %p")
            dfv = dfv[["full_name", "from_company", "person_to_meet", "Time"]]
            dfv.columns = ["Visitor Name", "Company", "Host", "Time"]
            dfv.index = dfv.index + 1

            st.dataframe(dfv, use_container_width=True, height=350)

    # ------------------ RIGHT SIDE: DEPARTMENTS ------------------
    with col_right:
        st.subheader("By Department")

        if not dept_count:
            st.info("No bookings today.")
        else:
            for dept, count in dept_count.items():
                st.markdown(
                    f"""
                    <div class="summary-card">
                        <div class="summary-title">{dept}</div>
                        <div class="summary-value">{count}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
