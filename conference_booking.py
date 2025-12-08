# ---------------- MY BOOKINGS ----------------
st.subheader("My Bookings")

bookings = get_user_bookings()
if not bookings:
    st.info("No bookings created yet.")
    return

for b in bookings:

    # ----------- EDIT MODE UI ----------- 
    if st.session_state.get(f"edit_{b['id']}", False):
        with st.container():
            st.markdown('<div class="edit-card">', unsafe_allow_html=True)
            st.subheader("Edit Booking")

            dt = b["booking_date"]
            slots = []
            t = datetime.combine(dt, WORK_START)
            end = datetime.combine(dt, WORK_END)

            while t <= end:
                slots.append(t.strftime("%I:%M %p"))
                t += timedelta(minutes=30)

            current_start = b["start_time"].strftime("%I:%M %p")
            current_end = b["end_time"].strftime("%I:%M %p")

            start_val = st.selectbox("Start Time", slots, index=slots.index(current_start), key=f"st_{b['id']}")
            end_val = st.selectbox("End Time", slots, index=slots.index(current_end), key=f"et_{b['id']}")

            st.markdown('<div class="purple-btn">', unsafe_allow_html=True)
            if st.button("Save Changes", key=f"s_{b['id']}"):
                ns = datetime.combine(dt, datetime.strptime(start_val, "%I:%M %p").time())
                ne = datetime.combine(dt, datetime.strptime(end_val, "%I:%M %p").time())

                if ne <= ns:
                    st.error("End time must be after start time.")
                else:
                    if update_booking(b['id'], dt, ns, ne):
                        st.success("Booking updated.")
                        st.session_state[f"edit_{b['id']}"] = False
                        st.rerun()

            if st.button("Cancel Editing", key=f"c_{b['id']}"):
                st.session_state[f"edit_{b['id']}"] = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        continue

    # ----------- NORMAL CARD UI -----------    
    with st.container():
        st.markdown('<div class="container-box">', unsafe_allow_html=True)

        colA, colB = st.columns(2)
        with colA:
            st.markdown(f"<div class='small-title'>Date:</div><div class='value'>{b['booking_date']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='small-title'>Time:</div><div class='value'>{b['start_time'].strftime('%I:%M %p')} - {b['end_time'].strftime('%I:%M %p')}</div>", unsafe_allow_html=True)

        with colB:
            st.markdown(f"<div class='small-title'>Department:</div><div class='value'>{b['department']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='small-title'>Purpose:</div><div class='value'>{b['purpose']}</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        b1, b2 = st.columns([1,1])
        with b1:
            st.markdown('<div class="purple-btn">', unsafe_allow_html=True)
            if st.button("Edit Booking", key=f"editbtn_{b['id']}"):
                st.session_state[f"edit_{b['id']}"] = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with b2:
            st.markdown('<div class="purple-btn">', unsafe_allow_html=True)
            if st.button("Cancel Booking", key=f"cancelbtn_{b['id']}"):
                delete_booking(b['id'])
                st.success("Booking cancelled.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
