import streamlit as st
from datetime import datetime
import base64
import pytz


def render_pass_page():
    # Timezone IST Fix
    IST = pytz.timezone("Asia/Kolkata")
    current_time = datetime.now(IST).strftime("%d-%m-%Y %H:%M")

    # Session Data
    visitor = st.session_state.get("pass_data")
    pass_image = st.session_state.get("pass_image")

    if not visitor or not pass_image:
        st.error("Pass data missing.")
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    # Left/Right layout
    col_pass, col_action = st.columns([3, 1.2])

    # ======================
    # VISITOR PASS (LEFT)
    # ======================
    with col_pass:

        st.markdown("""
        <style>
        .pass-card {
            background: #FFF;
            padding: 20px;
            border-radius: 14px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.12);
            width: 420px;
        }
        .pass-title {
            text-align: center;
            font-size: 28px;
            font-weight: 800;
            color: #4B2ECF;
            margin-bottom: 18px;
        }
        .pass-image img {
            width: 330px;
            border-radius: 12px;
            border: 4px solid #4B2ECF;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("<div class='pass-card'>", unsafe_allow_html=True)

        # Title
        st.markdown("<div class='pass-title'>Visitor Pass</div>", unsafe_allow_html=True)

        # Image
        img_data = base64.b64encode(pass_image).decode()
        st.markdown(
            f"""
            <div class='pass-image' style='text-align:center;'>
                <img src="data:image/jpeg;base64,{img_data}">
            </div>
            """,
            unsafe_allow_html=True
        )

        # Details
        st.markdown(
            f"""
            <div style="margin-top:15px;font-size:17px;">
                <p><b>Name:</b> {visitor['full_name']}</p>
                <p><b>Company:</b> {visitor['from_company']}</p>
                <p><b>To Meet:</b> {visitor['person_to_meet']}</p>
                <p><b>Visitor ID:</b> #{visitor['visitor_id']}</p>
                <p><b>Email:</b> {visitor['email']}</p>
                <p><b>Date:</b> {current_time}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # ======================
    # BUTTONS (RIGHT)
    # ======================
    with col_action:

        st.markdown("""
        <style>
        .vbtn button {
            background: linear-gradient(90deg, #4B2ECF, #7A42FF) !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
            font-size: 16px !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px !important;
            width: 100% !important;
            margin-bottom: 12px !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Dashboard (top)
        st.markdown("<div class='vbtn'>", unsafe_allow_html=True)
        if st.button("📊 Dashboard", key="pass_dashboard"):
            st.session_state["current_page"] = "visitor_dashboard"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Logout (below)
        st.markdown("<div class='vbtn'>", unsafe_allow_html=True)
        if st.button("🚪 Logout", key="pass_logout"):
            st.session_state.clear()
            st.session_state["current_page"] = "visitor_login"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
