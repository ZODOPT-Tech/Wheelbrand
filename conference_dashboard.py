import streamlit as st
import mysql.connector
import boto3
import json
from datetime import datetime

# ---------------- CONFIG -----------------
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"

AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"


# ---------------- AWS + DB -----------------
@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    secret = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    return json.loads(secret["SecretString"])


@st.cache_resource
def get_conn():
    creds = get_credentials()
    return mysql.connector.connect(
        host=creds["DB_HOST"],
        user=creds["DB_USER"],
        password=creds["DB_PASSWORD"],
        database=creds["DB_NAME"],
        autocommit=True
    )


# ---------------- FETCH BOOKINGS -----------------
def _get_bookings():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            cu.name AS booked_by,
            cu.department,
            cb.purpose,
            cb.start_time,
            cb.end_time
        FROM conference_bookings cb
        JOIN conference_users cu ON cu.id = cb.user_id
        ORDER BY cb.start_time DESC
    """)

    rows = cursor.fetchall()
    cursor.close()
    return rows


# ---------------- HEADER UI -----------------
def render_header():
    st.markdown(f"""
    <style>
        header[data-testid="stHeader"] {{
            display: none !important;
        }}

        .block-container {{
            padding-top: 0rem !important;
        }}

        .header-box {{
            background: {HEADER_GRADIENT};
            padding: 26px 40px;
            margin: 0px -1rem 2rem -1rem;
            border-radius: 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 6px 16px rgba(0,0,0,0.18);
        }}

        .header-title {{
            font-size: 32px;
            font-weight: 800;
            color: white;
            font-family: 'Inter', sans-serif;
            letter-spacing: 1px;
        }}

        .header-logo {{
            height: 52px;
        }}

        .summary-card {{
            background: white;
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.08);
            margin-bottom: 18px;
        }}

        .sum-title {{
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 6px;
        }}

        .sum-value {{
            font-size: 26px;
            font-weight: 800;
            color: #50309D;
        }}

        table {{
            width: 100%;
        }}

        th {{
            text-align: left;
            font-size: 15px;
            padding-bottom: 8px;
        }}

        td {{
            padding: 10px 0;
            font-size: 14px;
        }}
    </style>
    """, unsafe_allow_html=True)

    username = st.session_state.get("user_name", "User")

    st.markdown(f"""
        <div class="header-box">
            <div class="header-title">Welcome, {username}</div>
            <img src="{LOGO_URL}" class="header-logo">
        </div>
    """, unsafe_allow_html=True)


# ---------------- PAGE BODY -----------------
def render_dashboard():
    render_header()

    bookings = _get_bookings()

    # New Booking Button
    if st.button("➕ New Booking Registration", use_container_width=False):
        st.session_state['current_page'] = 'conference_bookings'
        st.rerun()

    st.write("")  # spacing

    col_left, col_right = st.columns([2, 1], gap="large")

    # LEFT: Booking Table
    with col_left:
        st.subheader("📋 Booking List")

        if not bookings:
            st.info("No bookings available.")
        else:
            # Table header
            st.markdown("""
            <table>
                <tr>
                    <th>Booked By</th>
                    <th>Department</th>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Purpose</th>
                </tr>
            """, unsafe_allow_html=True)

            # Table rows
            for b in bookings:
                date_str = b['start_time'].strftime("%d %b %Y")
                time_str = f"{b['start_time'].strftime('%H:%M')} - {b['end_time'].strftime('%H:%M')}"

                st.markdown(f"""
                <tr>
                    <td>{b['booked_by']}</td>
                    <td>{b['department']}</td>
                    <td>{date_str}</td>
                    <td>{time_str}</td>
                    <td>{b['purpose']}</td>
                </tr>
                """, unsafe_allow_html=True)

            st.markdown("</table>", unsafe_allow_html=True)

    # RIGHT: Summary
    with col_right:
        st.subheader("📊 Summary")

        today = datetime.today().date()

        today_count = len([b for b in bookings if b['start_time'].date() == today])
        total = len(bookings)

        # Today
        st.markdown(f"""
        <div class="summary-card">
            <div class="sum-title">Bookings Today</div>
            <div class="sum-value">{today_count}</div>
        </div>
        """, unsafe_allow_html=True)

        # Total
        st.markdown(f"""
        <div class="summary-card">
            <div class="sum-title">Total Bookings</div>
            <div class="sum-value">{total}</div>
        </div>
        """, unsafe_allow_html=True)

        # Per Department split
        dept_count = {}
        for b in bookings:
            dept_count[b['department']] = dept_count.get(b['department'], 0) + 1

        for d, c in dept_count.items():
            st.markdown(f"""
            <div class="summary-card">
                <div class="sum-title">{d}</div>
                <div class="sum-value">{c}</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("---")

    if st.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.session_state['current_page'] = 'conference_login'
        st.rerun()
