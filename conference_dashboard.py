import streamlit as st
from datetime import datetime


LOGO_URL = "https://raw.githubusercontent.com/ZODOPT-Tech/Wheelbrand/main/images/zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)"


def render_header(title: str):
    st.markdown(f"""
    <style>
        header[data-testid="stHeader"] {{
            display:none !important;
        }}

        .block-container {{
            padding-top:0rem !important;
        }}

        .header-box {{
            background:{HEADER_GRADIENT};
            padding:26px 40px;
            margin:0px -1rem 2rem -1rem;
            border-radius:18px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            box-shadow:0 6px 16px rgba(0,0,0,0.18);
        }}

        .header-title {{
            font-size:32px;
            font-weight:800;
            color:#fff;
            font-family:'Inter',sans-serif;
            letter-spacing:1px;
        }}

        .header-logo {{
            height:52px;
        }}

        .summary-card {{
            background:white;
            border-radius:18px;
            padding:18px;
            box-shadow:0 3px 12px rgba(0,0,0,0.08);
            margin-bottom:18px;
        }}

        .sum-title {{
            font-size:15px;
            font-weight:700;
            margin-bottom:6px;
        }}

        .sum-value {{
            font-size:26px;
            font-weight:800;
            color:#50309D;
        }}

        table {{
            width:100%;
        }}

        th {{
            text-align:left;
            font-size:15px;
            padding-bottom:8px;
        }}

        td {{
            padding:10px 0;
            font-size:14px;
        }}

        .new-btn {{
            background:#fff;
            padding:10px 16px;
            border:1px solid #ddd;
            border-radius:8px;
            font-weight:600;
        }}
    </style>

    <div class="header-box">
        <div class="header-title">{title}</div>
        <img src="{LOGO_URL}" class="header-logo">
    </div>
    """, unsafe_allow_html=True)


def render_booking_page():
    # Fake bookings list (this will be from DB)
    bookings = st.session_state.get("bookings", [])

    # Header
    render_header("Conference Booking")

    # NEW BOOKING BUTTON
    if st.button("➕ New Booking Registration", use_container_width=False):
        st.session_state['current_page'] = 'conference_new_booking'
        st.rerun()

    st.write("")  # spacing

    # MAIN CONTENT: 2 COLUMNS
    col_left, col_right = st.columns([2, 1], gap="large")

    # LEFT — BOOKINGS TABLE
    with col_left:
        st.subheader("📋 Booking List")

        if not bookings:
            st.info("No bookings available.")
        else:
            # Table headers
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

            # Table rows
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

    # RIGHT — METRICS CARDS
    with col_right:
        st.subheader("📊 Summary")

        today = datetime.today().date()
        today_count = len([b for b in bookings if b['start'].date() == today])
        total = len(bookings)

        st.markdown(f"""
        <div class="summary-card">
            <div class="sum-title">Bookings Today</div>
            <div class="sum-value">{today_count}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="summary-card">
            <div class="sum-title">Total Bookings</div>
            <div class="sum-value">{total}</div>
        </div>""", unsafe_allow_html=True)

        # Optional: Department Summary
        depts = {}
        for b in bookings:
            depts[b['dept']] = depts.get(b['dept'], 0) + 1

        if depts:
            for d, c in depts.items():
                st.markdown(f"""
                <div class="summary-card">
                    <div class="sum-title">{d}</div>
                    <div class="sum-value">{c}</div>
                </div>""", unsafe_allow_html=True)

    st.write("---")
    if st.button("← Back", use_container_width=True):
        st.session_state['current_page'] = 'conference_dashboard'
        st.rerun()
