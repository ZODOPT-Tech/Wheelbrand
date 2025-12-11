import streamlit as st
import mysql.connector
from datetime import datetime
import boto3
import json

# Try to use zoneinfo (Python 3.9+). Fallback gracefully if not available.
try:
    from zoneinfo import ZoneInfo
    ZONE_IST = ZoneInfo("Asia/Kolkata")
except Exception:
    ZoneInfo = None
    ZONE_IST = None

# ====================================================
# CONFIG
# ====================================================
AWS_REGION = "ap-south-1"
AWS_SECRET = "arn:aws:secretsmanager:ap-south-1:034362058776:secret:Wheelbrand-zM6npS"
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #4B2ECF, #7A42FF)"


# ====================================================
# AWS SECRETS
# ====================================================
@st.cache_resource
def get_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    raw = client.get_secret_value(SecretId=AWS_SECRET)
    return json.loads(raw["SecretString"])


# ====================================================
# DB CONNECTION
# ====================================================
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
# UTILS: datetime formatting to Asia/Kolkata (IST)
# ====================================================
def format_dt(dt):
    """
    Given a datetime object `dt` (naive or tz-aware), return a string
    formatted as 'DD-MM-YYYY HH:MM' in Asia/Kolkata timezone.

    - If dt is None -> return "—"
    - If dt is naive -> assume UTC and convert to Asia/Kolkata
      (this is common when DB stores UTC without tz info)
    - If zoneinfo is not available, fall back to dt.strftime as-is.
    """
    if not dt:
        return "—"

    try:
        # If dt is a string, attempt to parse (defensive)
        if isinstance(dt, str):
            try:
                # try ISO parse first
                dt = datetime.fromisoformat(dt)
            except Exception:
                # fallback: try common format
                try:
                    dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    return str(dt)

        # If zoneinfo available, convert properly
        if ZONE_IST is not None:
            if dt.tzinfo is None:
                # assume UTC for naive datetimes from DB
                from datetime import timezone
                dt_utc = dt.replace(tzinfo=timezone.utc)
            else:
                dt_utc = dt

            dt_ist = dt_utc.astimezone(ZONE_IST)
            return dt_ist.strftime("%d-%m-%Y %H:%M")
        else:
            # zoneinfo not available: best-effort naive formatting
            return dt.strftime("%d-%m-%Y %H:%M")
    except Exception:
        try:
            return str(dt)
        except Exception:
            return "—"


# ====================================================
# CSS
# ====================================================
def inject_css():
    st.markdown(f"""
    <style>
    header[data-testid="stHeader"] {{display:none;}}
    .block-container {{padding-top:0;}}

    .header-box {{
        background:{HEADER_GRADIENT};
        padding:24px 40px;
        border-radius:14px;
        margin-bottom:22px;
        display:flex;
        justify-content:space-between;
        align-items:center;
        box-shadow:0 4px 16px rgba(0,0,0,0.12);
    }}
    .head-title {{
        font-size:32px;
        font-weight:900;
        color:white;
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
        color:#4B2ECF;
    }}
    .new-btn button {{
        background:{HEADER_GRADIENT} !important;
        color:white !important;
        font-size:18px !important;
        font-weight:700 !important;
        border-radius:10px !important;
        width:100%;
        padding:14px 0px !important;
    }}
    </style>
    """, unsafe_allow_html=True)


# ====================================================
# DATA FETCHING
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
    rows = cur.fetchall()
    cur.close()
    return rows


def dashboard_counts(company_id):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT COUNT(*) AS c
        FROM visitors
        WHERE company_id=%s
          AND pass_generated=1
          AND DATE(registration_timestamp)=CURDATE()
    """, (company_id,))
    total = cur.fetchone()['c']

    cur.execute("""
        SELECT COUNT(*) AS c
        FROM visitors
        WHERE company_id=%s
          AND pass_generated=1
          AND checkout_time IS NULL
          AND DATE(registration_timestamp)=CURDATE()
    """, (company_id,))
    inside = cur.fetchone()['c']

    cur.execute("""
        SELECT COUNT(*) AS c
        FROM visitors
        WHERE company_id=%s
          AND pass_generated=1
          AND DATE(checkout_time)=CURDATE()
    """, (company_id,))
    out = cur.fetchone()['c']

    cur.close()
    return total, inside, out


def checkout(visitor_id):
    conn = get_conn()
    cur = conn.cursor()
    # Use Asia/Kolkata now for checkout timestamp
    try:
        if ZONE_IST is not None:
            now = datetime.now(tz=ZONE_IST)
        else:
            now = datetime.now()
        cur.execute("""
            UPDATE visitors 
            SET checkout_time=%s 
            WHERE visitor_id=%s
        """, (now, visitor_id))
        cur.close()
    except Exception:
        # Ensure cursor closed on error
        try:
            cur.close()
        except:
            pass
        raise


# ====================================================
# MAIN VISITOR DASHBOARD
# ====================================================
def render_dashboard():

    # -----------------------------------------
    # AUTH CHECK
    # -----------------------------------------
    if not st.session_state.get("admin_logged_in"):
        st.error("Unauthorized. Please login.")
        st.stop()

    inject_css()

    company = st.session_state.get("company_name", "Your Company")
    company_id = st.session_state.get("company_id")

    # -----------------------------------------
    # HEADER
    # -----------------------------------------
    st.markdown(f"""
        <div class="header-box">
            <div class="head-title">Welcome, {company}</div>
            <img src="{LOGO_URL}" height="55px">
        </div>
    """, unsafe_allow_html=True)

    # MAIN LAYOUT
    left, right = st.columns([4, 1.5])

    # -----------------------------------------
    # SUMMARY PANEL
    # -----------------------------------------
    with right:

        st.markdown("### 📊 Summary")
        total, inside, out = dashboard_counts(company_id)

        for label, val in [
            ("Visitors Today", total),
            ("Currently Inside", inside),
            ("Checked Out Today", out),
        ]:
            st.markdown(f"""
                <div class="summary-card">
                    <div class="summary-title">{label}</div>
                    <div class="summary-value">{val}</div>
                </div>
            """, unsafe_allow_html=True)

    # -----------------------------------------
    # LEFT CONTENT
    # -----------------------------------------
    with left:

        # NEW VISITOR BUTTON → GO TO PRIMARY DETAILS
        st.markdown("<div class='new-btn'>", unsafe_allow_html=True)
        if st.button("NEW VISITOR REGISTRATION"):
            st.session_state["registration_step"] = "primary"
            st.session_state["current_page"] = "visitor_primarydetails"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("## Visitor List")

        data = get_visitors(company_id)

        if not data:
            st.info("No visitors today.")
            return

        header = st.columns([3, 2, 2, 3, 2, 2])
        header[0].markdown("### Name")
        header[1].markdown("### Phone")
        header[2].markdown("### Meeting")
        header[3].markdown("### Visited")
        header[4].markdown("### Checkout")
        header[5].markdown("### Action")

        st.markdown("---")

        for v in data:
            vid = v["visitor_id"]

            # Format times to Asia/Kolkata
            reg_ts = format_dt(v.get("registration_timestamp"))
            checkout_time_str = format_dt(v.get("checkout_time"))

            row = st.columns([3, 2, 2, 3, 2, 2])
            row[0].write(v["full_name"])
            row[1].write(v["phone_number"])
            row[2].write(v["person_to_meet"])
            row[3].write(reg_ts)
            row[4].write(checkout_time_str)

            with row[5]:
                if not v["checkout_time"]:
                    if st.button("Checkout", key=f"out_{vid}"):
                        checkout(vid)
                        st.rerun()
                else:
                    st.markdown("<div class='summary-title'>Done</div>", unsafe_allow_html=True)
