import streamlit as st
import pandas as pd
from datetime import datetime

def render_dashboard():
    st.header("💻 Conference Dashboard")

    # Greeting
    user = st.session_state.get('user_name', 'Delegate')
    st.success(f"Welcome, {user}!")

    # --- Bookings Data ---
    bookings = st.session_state.get("bookings", [])
    today = datetime.today().date()
    todays = [b for b in bookings if b["start"].date() == today]

    total_bookings = len(bookings)
    today_bookings = len(todays)

    # Department-wise aggregation
    dept_stats = {}
    for b in bookings:
        dept = b.get("user_department", "Unknown")
        dept_stats[dept] = dept_stats.get(dept, 0) + 1

    # Who booked most
    user_count = {}
    for b in bookings:
        u = b.get("booked_by", "Unknown")
        user_count[u] = user_count.get(u, 0) + 1
    most_active_user = max(user_count, key=user_count.get) if user_count else None

    # ----- Summary Cards -----
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Bookings", total_bookings)
    col2.metric("Today's Bookings", today_bookings)

    if most_active_user:
        col3.metric("Top Booker", most_active_user)
    else:
        col3.metric("Top Booker", "N/A")

    st.write("---")

    # ----- Department Split -----
    st.subheader("📊 Bookings by Department")

    if dept_stats:
        dept_df = pd.DataFrame([
            {"Department": d, "Total Bookings": c}
            for d, c in dept_stats.items()
        ])
        st.table(dept_df)
    else:
        st.info("No department data yet.")

    st.write("---")

    # ----- Recent Bookings Table -----
    st.subheader("🕒 Recent Bookings")

    if bookings:
        recent = sorted(bookings, key=lambda x: x["timestamp"], reverse=True)[:5]
        recent_df = pd.DataFrame([
            {
                "Date": b["start"].date(),
                "Start": b["start"].strftime("%I:%M %p"),
                "End": b["end"].strftime("%I:%M %p"),
                "Purpose": b["purpose"],
                "Booked By": b.get("booked_by"),
                "User Department": b.get("user_department"),
            }
            for b in recent
        ])
        st.table(recent_df)
    else:
        st.info("No bookings done yet.")

    st.write("---")

    # ----- Navigation -----
    if st.button("🗓️ Manage Conference Bookings", type="primary", use_container_width=True):
        st.session_state['current_page'] = 'conference_bookings'
        st.rerun()

    st.write("---")

    if st.button("Logout"):
        st.session_state.clear()
        st.session_state['current_page'] = 'conference_login'
        st.rerun()
