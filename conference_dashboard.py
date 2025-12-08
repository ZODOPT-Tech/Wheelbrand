import streamlit as st
from datetime import datetime

# ---------------- CONFIG -----------------
LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


# ---------------- HEADER UI -----------------
def render_header():
    st.markdown(f"""
    <style>
        /* Hide default Streamlit header */
        header[data-testid="stHeader"] {{
            display: none !important;
        }}

        /* Move content up */
        .block-container {{
            padding-top: 0rem !important;
        }}

        /* Header Bar */
        .header-box {{
            background: {HEADER_GRADIENT};
            padding: 26px 40px;
            margin: 0px -1rem 2rem -1rem;
            border-radius: 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 6px 16px rgba(0,0,0,0.18);
        }}

        .header-title {{
            font-size: 32px;
            font-weight: 800;
            color: white;
            font-family: 'Inter', sans-serif;
            letter-spacing: 1px;
        }}

        .header-logo {{
            height: 52px;
        }}

        /* Summary Card */
        .summary-card {{
            background: white;
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.08);
            margin-bottom: 18px;
        }}

        .sum-title {{
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 6px;
        }}

        .sum-value {{
            font-size: 26px;
            font-weight: 800;
            color: #50309D;
        }}

        /* Table */
        table {{
            width: 100%;
        }}

        th {{
            text-align: left;
            font-size: 15px;
            padding-bottom: 8px;
        }}

        td {{
            padding: 10px 0;
            font-size: 14px;
        }}
    </style>
    """, unsafe_allow_html=True)

    username = st.session_state.get("user_name", "User")

    st.markdown(f"""
        <div class="header-box">
            <div class="header-title">Welcome, {username}</div>
            <img src="{LOGO_URL}" class="header-logo">
        </div>
    """, unsafe_allow_html=True)


# ---------------- PAGE BODY -----------------
def render_dashboard():
    # Render header
    render_header()

    # Fake bookings data
    bookings = st.session_state.get("bookings", [])

    # New Booking Button
    if st.button("➕ New Booking Registration", use_container_width=False):
        st.session_state['current_page'] = 'conference_bookings'
        st.rerun()

    st.write("")  # spacing

    # Layout: 2 columns
    col_left, col_right = st.columns([2, 1], gap="large")

    # LEFT SIDE: Booking List Table
    with col_left:
        st.subheader("📋 Booking List")

        if not bookings:
            st.info("No bookings available.")
        else:
            st.markdown("""
            <table>
                <tr>
                    <th>Booked By</th>
                    <th>Department</th>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Purpose</th>
                </tr>
            """, unsafe_allow_html=True)

            for b in bookings:
                st.markdown(f"""
                <tr>
                    <td>{b['user']}</td>
                    <td>{b['dept']}</td>
                    <td>{b['start'].date()}</td>
                    <td>{b['start'].strftime('%H:%M')} - {b['end'].strftime('%H:%M')}</td>
                    <td>{b['purpose']}</td>
                </tr>
                """, unsafe_allow_html=True)

            st.markdown("</table>", unsafe_allow_html=True)

    # RIGHT SIDE: Summary Metrics
    with col_right:
        st.subheader("📊 Summary")

        today = datetime.today().date()
        today_count = len([b for b in bookings if b['start'].date() == today])
        total = len(bookings)

        st.markdown(f"""
        <div class="summary-card">
            <div class="sum-title">Bookings Today</div>
            <div class="sum-value">{today_count}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="summary-card">
            <div class="sum-title">Total Bookings</div>
            <div class="sum-value">{total}</div>
        </div>
        """, unsafe_allow_html=True)

        # Department level summary
        depts = {}
        for b in bookings:
            depts[b['dept']] = depts.get(b['dept'], 0) + 1

        if depts:
            for d, c in depts.items():
                st.markdown(f"""
                <div class="summary-card">
                    <div class="sum-title">{d}</div>
                    <div class="sum-value">{c}</div>
                </div>
                """, unsafe_allow_html=True)

    st.write("---")

    # Logout
    if st.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.session_state['current_page'] = 'conference_login'
        st.rerun()
