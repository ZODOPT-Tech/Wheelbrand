import streamlit as st
import boto3, json, mysql.connector
from datetime import datetime
import pandas as pd

# ---------------- DB ----------------
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

# ---------------- UI ----------------
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"

def render_header(title):
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
    .header-logo {{
        height:48px;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="header-box">
        <div class="header-title">{title}</div>
        <img class="header-logo" src="{LOGO_URL}">
    </div>
    """, unsafe_allow_html=True)


# ---------------- Data Fetch ----------------
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


# ---------------- Page ----------------
def render_dashboard():
    render_header("CONFERENCE DASHBOARD")

    bookings = load_bookings()

    if st.button("➕ New Booking"):
        st.session_state['current_page'] = 'conference_bookings'
        st.rerun()

    col1, col2 = st.columns([2,1])

    with col1:
        st.subheader("Bookings")
        if not bookings:
            st.info("No bookings yet.")
        else:
            df = pd.DataFrame(bookings)
            df['date'] = df['booking_date'].astype(str)
            df['time'] = df['start_time'].dt.strftime("%H:%M") + " - " + df['end_time'].dt.strftime("%H:%M")
            st.dataframe(df[['name','department','date','time','purpose']], use_container_width=True)

    with col2:
        st.subheader("Insights")

        today = datetime.today().date()
        today_count = sum(b['booking_date'] == today for b in bookings)
        st.metric("Today", today_count)
        st.metric("Total", len(bookings))

        dept_count = {}
        for b in bookings:
            dept_count[b['department']] = dept_count.get(b['department'],0)+1

        for d,c in dept_count.items():
            st.metric(d, c)

    st.write("---")
    if st.button("Logout"):
        st.session_state.clear()
        st.session_state['current_page'] = 'conference_login'
        st.rerun()
