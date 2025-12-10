import streamlit as st
from datetime import datetime
import base64

# =============================
# CSS STYLE
# =============================
def load_css():
    st.markdown("""
        <style>
        .pass-card {
            width: 420px;
            margin: auto;
            background: #FFFFFF;
            padding: 25px;
            border-radius: 16px;
            box-shadow: 0 4px 18px rgba(0,0,0,0.12);
        }
        .pass-title {
            font-size: 32px;
            font-weight: 800;
            text-align: center;
            margin-bottom: 15px;
            color: #4B2ECF;
        }
        .photo-box {
            text-align:center;
            margin-bottom: 10px;
        }
        .photo-img {
            width:130px;
            height:130px;
            border-radius:10px;
            border:2px solid #4B2ECF;
        }
        .pass-item {
            font-size: 18px;
            margin:6px 0;
        }
        .label {
            font-weight:700;
        }
        .btn-box {
            width:420px;
            margin:auto;
            margin-top:30px;
            text-align:center;
        }
        .btn-box button {
            background:#4B2ECF !important;
            color:white !important;
            font-size:18px !important;
            padding:10px 18px !important;
            border-radius:8px !important;
            width:100% !important;
        }
        .msg-email {
            text-align:center;
            margin-top:10px;
            font-size:16px;
            font-weight:600;
            color:#4B2ECF;
        }
        </style>
    """, unsafe_allow_html=True)


# =============================
# MAIN PAGE
# =============================
def render_pass_page():
    load_css()

    # Check if data exists
    if "visitor_pass_data" not in st.session_state:
        st.error("No Visitor Pass Data Found")
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    data = st.session_state["visitor_pass_data"]

    # unpack
    visitor = data["visitor"]
    photo_bytes = data["photo_bytes"]

    # image base64
    img_b64 = base64.b64encode(photo_bytes).decode()

    st.markdown("<div class='pass-title'>Visitor Pass</div>", unsafe_allow_html=True)

    # ===== PASS CARD =====
    st.markdown("<div class='pass-card'>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="photo-box">
            <img class='photo-img' src="data:image/jpeg;base64,{img_b64}">
        </div>

        <p class='pass-item'><span class='label'>Name:</span> {visitor['full_name']}</p>
        <p class='pass-item'><span class='label'>Company:</span> {visitor['from_company']}</p>
        <p class='pass-item'><span class='label'>To Meet:</span> {visitor['person_to_meet']}</p>
        <p class='pass-item'><span class='label'>Visitor ID:</span> #{visitor['visitor_id']}</p>
        <p class='pass-item'><span class='label'>Date:</span> {datetime.now().strftime("%d-%m-%Y %H:%M")}</p>
        """,
        unsafe_allow_html=True,
    )

    # close card
    st.markdown("</div>", unsafe_allow_html=True)

    # Email Message
    st.markdown(
        f"<p class='msg-email'>📧 Pass sent to Email address: <b>{visitor['email']}</b></p>",
        unsafe_allow_html=True
    )

    # Buttons
    st.markdown("<div class='btn-box'>", unsafe_allow_html=True)

    if st.button("➕ New Visitor"):
        st.session_state.pop("visitor_pass_data", None)
        st.session_state["registration_step"] = "primary"
        st.session_state["current_page"] = "visitor_details"
        st.rerun()

    if st.button("📊 Dashboard"):
        st.session_state.pop("visitor_pass_data", None)
        st.session_state["current_page"] = "visitor_dashboard"
        st.rerun()

    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.session_state["current_page"] = "visitor_login"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# router export
def render_pass():
    return render_pass_page()
