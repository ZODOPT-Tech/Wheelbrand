import streamlit as st
import os

# Path for your logo (GitHub RAW URL recommended)
LOGO_PATH = "zodopt.png"

HEADER_GRADIENT = "linear-gradient(90deg, #4B2ECF, #7A42FF)"

# ---------------------- CUSTOM CSS ----------------------
def load_dashboard_css():
    st.markdown(f"""
    <style>

    .stApp > header {{visibility: hidden;}}

    /* Header */
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

    /* Dashboard Button Styling */
    .stButton > button {{
        background: {HEADER_GRADIENT} !important;
        color: white !important;
        border-radius: 12px !important;
        width: 100% !important;
        padding: 16px 0 !important;
        font-size: 20px !important;
        font-weight: 700 !important;
        border: none !important;
    }}
    .stButton > button:hover {{
        opacity: 0.92 !important;
    }}

    /* Card Styling */
    .dashboard-card {{
        background: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0px 4px 18px rgba(0,0,0,0.09);
        margin-bottom: 25px;
        font-size: 18px;
        line-height: 1.6;
    }}

    .label-text {{
        font-size: 16px;
        font-weight: 600;
        color: #555;
        margin-bottom: 6px;
    }}

    .value-text {{
        font-size: 18px;
        font-weight: 700;
        color: #333;
        margin-bottom: 10px;
    }}

    </style>
    """, unsafe_allow_html=True)


# ---------------------- HEADER ----------------------
def render_header():
    if os.path.exists(LOGO_PATH):
        logo_html = f'<img src="{LOGO_PATH}" class="header-logo">'
    else:
        logo_html = '<div style="font-size:24px;color:white;font-weight:900">zodopt</div>'

    st.markdown(
        f"""
        <div class="header-box">
            <div class="header-title">VISITOR MANAGEMENT DASHBOARD</div>
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------- MAIN DASHBOARD ----------------------
def render_visitor_dashboard():

    if "admin_logged_in" not in st.session_state or not st.session_state["admin_logged_in"]:
        st.error("Access Denied: Please login.")
        st.stop()

    # Load CSS + Header
    load_dashboard_css()
    render_header()

    company_id = st.session_state.get("company_id", "N/A")
    admin_name = st.session_state.get("admin_name", "Admin")

    # Dashboard Welcome Card
    st.markdown(
        f"""
        <div class="dashboard-card">
            <div class="label-text">Welcome</div>
            <div class="value-text">{admin_name}</div>

            <div class="label-text">Company ID</div>
            <div class="value-text">{company_id}</div>

            <hr>

            <div style="font-size:17px;color:#555;">
                Use the button below to begin a new visitor registration.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # New Registration Button
    if st.button("➕ NEW VISITOR REGISTRATION"):
        st.session_state["current_page"] = "visitor_registration"  # loads visitor_details.py
        st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

    # OPTIONAL: You can add more cards showing counts, history, etc.


# ---------------------- ENTRY POINT ----------------------
if __name__ == "__main__":
    render_visitor_dashboard()

