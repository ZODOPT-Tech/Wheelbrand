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
def render_header(company_name):
    st.markdown(f"""
    <style>
        header[data-testid="stHeader"] {{display:none!important;}}
        .block-container {{padding-top:0rem!important;}}

        .header-box {{
            background:{HEADER_GRADIENT};
            padding:24px 38px;
            margin:-1rem -1rem 1.5rem -1rem;
            border-radius:18px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            box-shadow:0 6px 16px rgba(0,0,0,0.18);
        }}
        .header-title {{
            font-size:28px;
            font-weight:800;
            color:white;
        }}
        .header-sub {{
            font-size:15px;
            color:white;
            margin-top:4px;
            opacity:0.85;
        }}
        .header-right {{
            display:flex;
            align-items:center;
            gap:18px;
        }}
        .logout-btn {{
            background:transparent;
            border:none;
            cursor:pointer;
        }}
        .logout-icon {{
            width:30px;
            filter:brightness(95%);
        }}
        .header-logo {{
            height:48px;
        }}
    </style>
    """, unsafe_allow_html=True)

    username = st.session_state.get("user_name", "")
    
    st.markdown(f"""
    <div class="header-box">
        <div>
            <div class="header-title">Welcome, {username}</div>
            <div class="header-sub">{company_name} Dashboard</div>
        </div>

        <div class="header-right">
            <img class="header-logo" src="{LOGO_URL}">
            <form action="" method="post">
                <button class="logout-btn" name="logout">
                    <img class="logout-icon" src="https://cdn-icons-png.flaticon.com/512/1828/1828490.png"/>
                </button>
            </form>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Logout handler
    if "logout" in st.session_state.get('form_submitter', {}):
        st.session_state.clear()
        st.session_state['current_page'] = "conference_login"
        st.rerun()


# -------------------- FETCH DATA --------------------
def load_company_bookings(company):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.*, u.name AS employee_name, u.department
        FROM conference_bookings b
        JOIN conference_users u ON u.id = b.user_id
        WHERE u.company = %s
        ORDER BY b.start_time DESC
    """, (company,))
    return cursor.fetchall()


# -------------------- DASHBOARD --------------------
def render_dashboard():
    # Current user details
    company = st.session_state.get("company", None)

    # HEADER
    render_header(company)

    # DATA
    bookings = load_company_bookings(company)

    # TOP ACTION BUTTON
    st.write("")  # spacing
    if st.button("New Booking Registration", use_container_width=True):
        st.session_state['current_page'] = 'conference_bookings'
        st.rerun()

    st.write("")  # spacing

    # LAYOUT
    col_left, col_right = st.columns([2, 1])

    # LEFT: Booking Table
    with col_left:
        st.subheader("Booking List")
        if not bookings:
            st.info("No bookings available.")
        else:
            df = pd.DataFrame(bookings)
            df["Date"] = df["start_time"].dt.date
            df["Time"] = df["start_time"].dt.strftime("%I:%M %p") + " - " + df["end_time"].dt.strftime("%I:%M %p")

            df = df[["employee_name", "department", "Date", "Time", "purpose"]]
            df.columns = ["Booked By", "Department", "Date", "Time", "Purpose"]

            st.dataframe(
                df,
                use_container_width=True,
                height=410
            )

    # RIGHT: Metrics
    with col_right:
        st.subheader("Summary Overview")

        today = datetime.today().date()
        today_count = len([b for b in bookings if b["booking_date"] == today])
        st.metric("Bookings Today", today_count)

        st.metric("Total Bookings", len(bookings))

        # Department Metrics
        st.write("---")
        dept_counts = {}
        for b in bookings:
            d = b['department']
            dept_counts[d] = dept_counts.get(d, 0) + 1

        for dept, count in dept_counts.items():
            st.metric(dept, count)
