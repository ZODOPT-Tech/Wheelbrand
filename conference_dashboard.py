import streamlit as st
import boto3
import json
import mysql.connector
from datetime import datetime
import pandas as pd

# -------------------- AWS DB CONFIG --------------------
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

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


# -------------------- UI CONFIG --------------------
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


# -------------------- HEADER --------------------
def render_header():
    st.markdown(f"""
    <style>
    header[data-testid="stHeader"]{{display:none!important;}}
    .block-container{{padding-top:0rem!important;}}
    .header-box {{
        background:{HEADER_GRADIENT};
        padding:24px 36px;
        margin:-1rem -1rem 1rem -1rem;
        border-radius:18px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 6px 16px rgba(0,0,0,0.18);
    }}
    .header-title {{
        font-size:30px;
        font-weight:800;
        color:white;
    }}
    .header-logo {{height:48px;}}
    </style>
    """, unsafe_allow_html=True)

    username = st.session_state.get("user_name", "User")
    st.markdown(f"""
    <div class="header-box">
        <div class="header-title">Welcome, {username}</div>
        <img class="header-logo" src="{LOGO_URL}">
    </div>
    """, unsafe_allow_html=True)


# -------------------- FETCH DATA --------------------
def load_bookings():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.*, u.name, u.department
        FROM conference_bookings b
        JOIN conference_users u ON u.id = b.user_id
        ORDER BY b.start_time DESC
    """)
    return cursor.fetchall()


# -------------------- DASHBOARD --------------------
def render_dashboard():
    render_header()

    bookings = load_bookings()

    if st.button("➕ New Booking Registration"):
        st.session_state['current_page'] = 'conference_bookings'
        st.rerun()

    col_left, col_right = st.columns([2,1])

    with col_left:
        st.subheader("📋 Booking List")
        if not bookings:
            st.info("No bookings available.")
        else:
            df = pd.DataFrame(bookings)
            df["meeting_date"] = df["start_time"].dt.date
            df["time"] = df["start_time"].dt.strftime("%H:%M") + " - " + df["end_time"].dt.strftime("%H:%M")
            st.dataframe(df[["name","department","meeting_date","time","purpose"]],
                         use_container_width=True)

    with col_right:
        st.subheader("📊 Summary")
        today = datetime.today().date()
        today_count = len([b for b in bookings if b["booking_date"] == today])
        st.metric("Today's Bookings", today_count)
        st.metric("Total Bookings", len(bookings))

        dept_map = {}
        for b in bookings:
            dept_map[b['department']] = dept_map.get(b['department'],0)+1

        for d,c in dept_map.items():
            st.metric(d, c)

    st.write("---")
    if st.button("Logout"):
        st.session_state.clear()
        st.session_state['current_page'] = 'conference_login'
        st.rerun()
