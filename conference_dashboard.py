import streamlit as st
import boto3
import json
import mysql.connector
from datetime import datetime
import pandas as pd
import pytz
from collections import Counter
import altair as alt # Added for advanced charting

# -------------------------------------------------------
# AWS & DB CONFIG
# -------------------------------------------------------
AWS_REGION = "ap-south-1"
AWS_SECRET_NAME = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"

# Define the timezone for display (Crucial for professional time management)
TIMEZONE = pytz.timezone("Asia/Kolkata")

@st.cache_resource
def get_credentials():
    """Fetches database credentials from AWS Secrets Manager."""
    try:
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        secret = client.get_secret_value(SecretId=AWS_SECRET_NAME)
        return json.loads(secret["SecretString"])
    except Exception as e:
        st.error(f"Failed to fetch AWS credentials: {e}")
        return {}


@st.cache_resource
def get_conn():
    """Establishes and returns a MySQL database connection."""
    creds = get_credentials()
    if not creds:
        return None
    try:
        return mysql.connector.connect(
            host=creds["DB_HOST"],
            user=creds["DB_USER"],
            password=creds["DB_PASSWORD"],
            database=creds["DB_NAME"],
            autocommit=True
        )
    except mysql.connector.Error as err:
        st.error(f"Database connection error: {err}")
        return None


# -------------------------------------------------------
# UI CONFIG
# -------------------------------------------------------
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
PRIMARY_COLOR = "#7A42FF"
SECONDARY_COLOR = "#50309D"


# -------------------------------------------------------
# GLOBAL CSS (Simplified and Enhanced for a modern look)
# -------------------------------------------------------
def set_global_css():
    """Sets application-wide CSS for a clean, modern look."""
    st.markdown(f"""
    <style>
    /* 1. Remove Streamlit Header and Adjust Padding */
    header[data-testid="stHeader"] {{display: none;}}
    .block-container {{padding-top: 1rem;}}
    
    /* 2. Custom Header Box */
    .header-box {{
        background: linear-gradient(90deg, {SECONDARY_COLOR}, {PRIMARY_COLOR});
        padding: 24px 30px;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
    }}

    .header-title {{
        font-size: 32px;
        font-weight: 700;
        color: white;
        margin-bottom: 5px;
    }}

    .header-sub {{
        font-size: 18px;
        font-weight: 400;
        color: rgba(255, 255, 255, 0.9);
    }}

    .header-logo {{height: 48px;}}
    
    .logout-icon {{
        width: 32px;
        cursor: pointer;
        transition: 0.3s;
    }}
    .logout-icon:hover {{
        filter: drop-shadow(0 0 5px rgba(255, 255, 255, 0.7));
    }}

    /* 3. Hide Streamlit's default button appearance */
    .hidden-button {{
        visibility: hidden !important;
        height: 0px !important;
        width: 0px !important;
        padding: 0 !important;
        margin: 0 !important;
    }}
    
    /* 4. Enhancement for Metrics (Card Style) */
    [data-testid="stMetric"] {{
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
    }}
    
    /* 5. Custom button styling (New Booking) */
    .stButton>button {{
        background-color: {PRIMARY_COLOR};
        color: white;
        font-weight: 600;
        border-radius: 10px;
        padding: 10px 20px;
        border: none;
        transition: 0.3s;
    }}
    .stButton>button:hover {{
        background-color: {SECONDARY_COLOR};
    }}
    
    </style>
    """, unsafe_allow_html=True)


# -------------------------------------------------------
# HEADER & LOGOUT
# -------------------------------------------------------
def _handle_logout():
    """Handles the logout logic."""
    st.session_state.clear()
    st.session_state["current_page"] = "conference_login" 
    st.rerun()

def render_header():
    """Renders the custom, gradient-filled application header."""
    username = st.session_state.get("user_name", "User")
    company = st.session_state.get("company", "Company Dashboard")

    st.markdown(f"""
        <div class="header-box">
            <div class="header-left">
                <div class="header-title">Conference Room Dashboard</div>
                <div class="header-sub">Welcome, **{username}** ({company})</div>
            </div>

            <div class="header-right">
                <img class="header-logo" src="{LOGO_URL}"/>

                <img class="logout-icon"
                     src="https://cdn-icons-png.flaticon.com/512/1828/1828490.png"
                     title="Logout"
                     onclick="document.getElementById('logout_trigger').click();"/>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # hidden logout button for Streamlit to handle the callback
    logout_btn = st.button("logout", key="logout_trigger", help="", on_click=_handle_logout)
    st.markdown('<div class="hidden-button"></div>', unsafe_allow_html=True)


# -------------------------------------------------------
# FETCH BOOKINGS
# -------------------------------------------------------
@st.cache_data(ttl=600) # Cache data for 10 minutes to improve performance
def load_company_bookings(company):
    """Fetches all conference room bookings for the given company."""
    conn = get_conn()
    if conn is None:
        return []
        
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, u.name AS employee_name, u.department
            FROM conference_bookings b
            JOIN conference_users u ON u.id = b.user_id
            WHERE u.company = %s
            ORDER BY b.start_time DESC
        """, (company,))
        bookings = cursor.fetchall()
        cursor.close()
        return bookings
    except mysql.connector.Error as err:
        st.error(f"Error fetching bookings: {err}")
        return []


# -------------------------------------------------------
# DASHBOARD PAGE
# -------------------------------------------------------
def render_dashboard():
    """Renders the main dashboard view."""

    set_global_css()
    render_header()
    
    # Data Loading
    company = st.session_state.get("company")
    if not company:
        st.warning("Please log in to view the dashboard.")
        return

    bookings = load_company_bookings(company)
    
    # Action Button
    if st.button("➕ **New Booking**", use_container_width=True):
        st.session_state["current_page"] = "conference_bookings"
        st.rerun()

    st.divider()

    col_left, col_right = st.columns([2, 1])

    # LEFT : Booking Table (Primary View)
    with col_left:
        st.subheader("Recent Bookings")
        
        if not bookings:
            st.info("No conference room bookings found for your company.")
        else:
            # Data Transformation with Timezone consideration
            df = pd.DataFrame(bookings)
            
            # Convert times to local timezone
            df["start_time_local"] = pd.to_datetime(df["start_time"]).dt.tz_localize(pytz.utc).dt.tz_convert(TIMEZONE)
            df["end_time_local"] = pd.to_datetime(df["end_time"]).dt.tz_localize(pytz.utc).dt.tz_convert(TIMEZONE)

            df["Date"] = df["start_time_local"].dt.date
            df["Time Range"] = (
                df["start_time_local"].dt.strftime("%I:%M %p")
                + " - " +
                df["end_time_local"].dt.strftime("%I:%M %p")
            )
            df["Employee"] = df["employee_name"]
            
            display_df = df[[
                "Employee", 
                "department", 
                "Date", 
                "Time Range", 
                "purpose"
            ]]
            
            display_df.columns = [
                "Booked By", 
                "Dept.", 
                "Date", 
                "Time", 
                "Purpose"
            ]

            # Use st.dataframe with better configuration
            st.dataframe(
                display_df, 
                use_container_width=True, 
                height=450,
                column_config={
                    "Booked By": st.column_config.TextColumn("Booked By"),
                    "Purpose": st.column_config.TextColumn("Purpose", help="Purpose of the booking"),
                },
                hide_index=True
            )


    # RIGHT : Metrics and Visualizations (Summary)
    with col_right:
        st.subheader("Usage Summary")
        
        if not bookings:
            st.info("No data to summarize.")
            return

        # Top-Level Metrics
        today_local = datetime.now(TIMEZONE).date()
        today_bookings = [
            b for b in bookings 
            if pd.to_datetime(b["start_time"]).tz_localize(pytz.utc).tz_convert(TIMEZONE).date() == today_local
        ]
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.metric("**Today's Count**", len(today_bookings), delta_color="normal")
        with col_t2:
            st.metric("**Total Bookings**", len(bookings))

        st.markdown("---")
        
        # Breakdown Visualizations
        st.write("#### By Department")

        # By Department - Bar Chart
        dept_counts = Counter(b["department"] for b in bookings)
        dept_df = pd.DataFrame(dept_counts.items(), columns=['Department', 'Count'])
        st.bar_chart(dept_df.set_index('Department'), color=PRIMARY_COLOR)
        
        st.markdown("---")
        st.write("#### By Purpose")
        
        # By Purpose - Donut Chart
        purpose_counts = Counter(b["purpose"] for b in bookings)
        purpose_df = pd.DataFrame(purpose_counts.items(), columns=['Purpose', 'Count'])
        
        base = alt.Chart(purpose_df).encode(
            theta=alt.Theta("Count:Q", stack=True)
        ).properties(height=200)

        pie = base.mark_arc(outerRadius=100, innerRadius=50).encode(
            color=alt.Color("Purpose:N"),
            order=alt.Order("Count:Q", sort="descending"),
            tooltip=["Purpose", "Count"]
        )

        st.altair_chart(pie, use_container_width=True)

# -------------------------------------------------------
# START APP (Conceptual)
# -------------------------------------------------------
# if st.session_state.get("current_page") == "conference_dashboard":
#     render_dashboard()
