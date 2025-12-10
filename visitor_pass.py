import streamlit as st
from datetime import datetime
import base64


# ==============================
# PASS PAGE UI STYLING
# ==============================
def load_pass_css():
    st.markdown("""
        <style>
        .pass-container {
            width: 420px;
            margin: 0 auto;
            background: #FFFFFF;
            border-radius: 14px;
            padding: 24px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.12);
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
            margin-bottom: 14px;
        }
        .pass-photo img {
            width: 150px;
            height: 150px;
            border-radius: 12px;
            border: 3px solid #4B2ECF;
            object-fit: cover;
        }

        .pass-field {
            font-size: 16px;
            margin: 6px 0;
        }
        .label {
            font-weight: 700;
            color: #444;
        }

        .email-note {
            text-align: center;
            margin-top: 15px;
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


# ==============================
# RENDER PASS PAGE
# ==============================
def render_pass_page():

    # ------------- SECURITY CHECKS -------------
    if not st.session_state.get("email_sent", False):
        st.error("Invalid access. Email not sent.")
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    if "pass_data" not in st.session_state:
        st.error("Visitor data not found.")
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    visitor = st.session_state["pass_data"]

    load_pass_css()

    # ------------- PASS CARD -------------
    st.markdown("<div class='pass-container'>", unsafe_allow_html=True)
    st.markdown("<div class='pass-title'>Visitor Pass</div>", unsafe_allow_html=True)

    # photo
    base64_img = base64.b64encode(visitor["photo_bytes"]).decode()
    st.markdown(f"""
        <div class="pass-photo">
            <img src="data:image/jpeg;base64,{base64_img}">
        </div>
    """, unsafe_allow_html=True)

    # visitor details
    st.markdown(f"""
        <div class="pass-field"><span class="label">Name:</span> {visitor['full_name']}</div>
        <div class="pass-field"><span class="label">Company:</span> {visitor['from_company']}</div>
        <div class="pass-field"><span class="label">To Meet:</span> {visitor['person_to_meet']}</div>
        <div class="pass-field"><span class="label">Visitor ID:</span> #{visitor['visitor_id']}</div>
        <div class="pass-field"><span class="label">Email Sent To:</span> {visitor['email']}</div>
        <div class="pass-field"><span class="label">Date:</span> {datetime.now().strftime('%d-%m-%Y %H:%M')}</div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # email confirmation text
    st.markdown(
        f"<div class='email-note'>Pass sent to: <b>{visitor['email']}</b></div>",
        unsafe_allow_html=True
    )

    st.write("")
    st.write("")

    # ------------- CENTERED ACTION BUTTONS -------------
    col_spacer_left, col_dashboard, col_logout, col_spacer_right = st.columns([1, 2, 2, 1])

    # Dashboard
    with col_dashboard:
        st.markdown("<div class='action-btn'>", unsafe_allow_html=True)
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state["current_page"] = "visitor_dashboard"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Logout
    with col_logout:
        st.markdown("<div class='action-btn'>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.session_state["current_page"] = "visitor_login"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
