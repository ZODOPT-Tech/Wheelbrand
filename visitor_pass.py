import streamlit as st
from datetime import datetime
import base64


# ===========================
# PASS PAGE UI CSS
# ===========================
def load_pass_css():
    st.markdown("""
        <style>

        .pass-container {
            width: 430px;
            margin: 0 auto;
            background: #FFFFFF;
            border-radius: 14px;
            padding: 26px 24px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.12);
        }

        .pass-logo {
            text-align: center;
            margin-bottom: 12px;
        }
        .pass-logo img {
            height: 60px;
        }

        .pass-title {
            text-align: center;
            font-size: 28px;
            font-weight: 800;
            color: #4B2ECF;
            margin-bottom: 20px;
        }

        .pass-photo {
            text-align: center;
            margin-bottom: 18px;
        }
        .pass-photo img {
            width: 165px;
            height: 165px;
            border-radius: 12px;
            border: 3px solid #4B2ECF;
            object-fit: cover;
        }

        .pass-field {
            font-size: 17px;
            margin: 6px 0;
        }
        .label {
            font-weight: 700;
            color: #222;
        }

        .email-note {
            text-align: center;
            margin-top: 14px;
            color: #4B2ECF;
            font-weight: 600;
            font-size: 15px;
        }

        .action-btn button {
            width: 100%;
            background: linear-gradient(90deg, #4B2ECF, #7A42FF) !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 10px !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            border: none !important;
        }

        </style>
    """, unsafe_allow_html=True)


# ===========================
# PASS PAGE
# ===========================
def render_pass_page():
    load_pass_css()

    visitor = st.session_state.get("pass_data")
    if not visitor:
        st.error("⚠️ Pass data not found.")
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    # ===========================
    # PASS CARD
    # ===========================
    st.markdown("<div class='pass-container'>", unsafe_allow_html=True)

    # --- LOGO ---
    st.markdown(f"""
        <div class="pass-logo">
            <img src="https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png">
        </div>
    """, unsafe_allow_html=True)

    # --- TITLE ---
    st.markdown("<div class='pass-title'>Visitor Pass</div>", unsafe_allow_html=True)

    # --- PHOTO ---
    base64_img = base64.b64encode(visitor["photo_bytes"]).decode()
    st.markdown(f"""
        <div class="pass-photo">
            <img src="data:image/jpeg;base64,{base64_img}">
        </div>
    """, unsafe_allow_html=True)

    # --- DETAILS ---
    st.markdown(f"""
        <div class="pass-field"><span class="label">Name:</span> {visitor['full_name']}</div>
        <div class="pass-field"><span class="label">Company:</span> {visitor['from_company']}</div>
        <div class="pass-field"><span class="label">To Meet:</span> {visitor['person_to_meet']}</div>
        <div class="pass-field"><span class="label">Visitor ID:</span> #{visitor['visitor_id']}</div>
        <div class="pass-field"><span class="label">Email Sent To:</span> {visitor['email']}</div>
        <div class="pass-field"><span class="label">Date:</span> {datetime.now().strftime('%d-%m-%Y %H:%M')}</div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ===========================
    # STATUS TEXT
    # ===========================
    st.markdown(
        f"<div class='email-note'>Pass sent to: <b>{visitor['email']}</b></div>",
        unsafe_allow_html=True
    )

    st.write("")
    st.write("")

    # ===========================
    # ACTION BUTTONS
    # ===========================
    col_spacer_left, col_dash, col_log, col_spacer_right = st.columns([1, 2, 2, 1])

    # Dashboard
    with col_dash:
        st.markdown("<div class='action-btn'>", unsafe_allow_html=True)
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state["current_page"] = "visitor_dashboard"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Logout
    with col_log:
        st.markdown("<div class='action-btn'>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.session_state["current_page"] = "visitor_login"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
