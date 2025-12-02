import streamlit as st
import os

# ===========================
# REFRESH REDIRECT PROTECTION
# ===========================
# 🚨 If user refreshes this page directly, force redirect to main_screen.py
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "main_screen"
    st.rerun()

# ===========================
# CONFIGURATION
# ===========================

# ⭐ Update GitHub raw logo URL
LOGO_PATH = "https://raw.githubusercontent.com/<USERNAME>/<REPO>/main/zodopt.png"

HEADER_GRADIENT = "linear-gradient(90deg, #4B2ECF, #7A42FF)"


# ===========================
# CUSTOM CSS
# ===========================

def load_dashboard_css():
    st.markdown(f"""
    <style>

    .stApp > header {{visibility: hidden;}}

    /* HEADER */
    .header-box {{
        background: {HEADER_GRADIENT};
        padding: 26px 45px;
        border-radius: 12px;
        max-width: 1600px;
        width: 100%;
        margin: 0 auto 35px auto;

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
        object-fit: contain;
    }}

    /* MAIN BUTTON */
    .stButton > button {{
        background: {HEADER_GRADIENT} !important;
        color: white !important;
        border-radius: 12px !important;
        width: 100% !important;
        padding: 18px 0 !important;
        font-size: 20px !important;
        font-weight: 700 !important;
        border: none !important;
        margin-top: 10px !important;
    }}
    .stButton > button:hover {{
        opacity: 0.92 !important;
    }}

    /* DASHBOARD CARD */
    .dashboard-card {{
        background: white;
        padding: 28px;
        border-radius: 14px;
        box-shadow: 0px 4px 18px rgba(0,0,0,0.10);
        margin-bottom: 25px;
    }}

    .welcome-title {{
        font-size: 28px;
        font-weight: 800;
        color: #222;
    }}

    .company-label {{
        font-size: 16px;
        font-weight: 600;
        color: #666;
        margin-top: 15px;
    }}

    .company-value {{
        font-size: 20px;
        font-weight: 700;
        color: #333;
        margin-bottom: 15px;
    }}

    </style>
    """, unsafe_allow_html=True)


# ===========================
# HEADER
# ===========================

def render_header():
    # Display GitHub logo if valid URL
    if LOGO_PATH.startswith("http"):
        logo_html = f'<img src="{LOGO_PATH}" class="header-logo">'
    else:
        logo_html = '<div style="color:white;font-size:24px;font-weight:900">zodopt</div>'

    st.markdown(f"""
        <div class="header-box">
            <div class="header-title">VISITOR MANAGEMENT DASHBOARD</div>
            {logo_html}
        </div>
    """, unsafe_allow_html=True)


# ===========================
# MAIN DASHBOARD CONTENT
# ===========================

def render_visitor_dashboard():

    # Access check
    if "admin_logged_in" not in st.session_state or not st.session_state["admin_logged_in"]:
        st.error("Access Denied: Please login.")
        st.stop()

    load_dashboard_css()
    render_header()

    admin_name = st.session_state.get("admin_name", "Admin")
    company_id = st.session_state.get("company_id", "N/A")

    # ---------------------------
    # CLEAN HTML CARD BLOCK
    # ---------------------------

    card_html = f"""
    <div class="dashboard-card">

        <div class="welcome-title">
            Welcome, {admin_name}
        </div>

        <div class="company-label">Company ID</div>
        <div class="company-value">{company_id}</div>

        <hr style="margin:20px 0;">

        <div style="font-size:17px; color:#555;">
            Use the button below to begin a new visitor registration.
        </div>

    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)

    # ---------------------------
    # BUTTON → visitor_registration
    # ---------------------------
    if st.button("➕ NEW VISITOR REGISTRATION"):
        st.session_state["current_page"] = "visitor_registration"
        st.rerun()


# ===========================
# EXPORT FOR ROUTER
# ===========================

def render_dashboard():
    return render_visitor_dashboard()


# ===========================
# DEBUG MODE
# ===========================
if __name__ == "__main__":
    st.session_state["admin_logged_in"] = True
    st.session_state["admin_name"] = "Test Admin"
    st.session_state["company_id"] = 1

    render_visitor_dashboard()
