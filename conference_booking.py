import streamlit as st

def render_booking_page():
    st.subheader("📅 Conference Room Bookings")
    
    tab1, tab2 = st.tabs(["View Schedule", "Book a Slot"])
    
    with tab1:
        st.write("Current Booking Schedule:")
        st.dataframe({
            "Room": ["Hall 1", "Meeting Room A", "Hall 1", "Meeting Room B"],
            "Time": ["9:00 AM", "11:00 AM", "2:00 PM", "3:00 PM"],
            "Topic": ["Keynote", "Delegate Mtg", "Panel Discussion", "Networking"],
            "Status": ["Booked", "Available", "Booked", "Available"]
        }, use_container_width=True)

    with tab2:
        st.write("Reserve a Private Meeting Room:")
        st.selectbox("Select Room:", ["Meeting Room A", "Meeting Room B", "Quiet Zone"])
        st.time_input("Start Time:")
        st.button("Confirm Reservation")

    st.divider()
    if st.button("← Back to Dashboard"):
        st.session_state['current_page'] = 'conference_dashboard'
        st.rerun()