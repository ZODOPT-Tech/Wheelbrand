import streamlit as st
import datetime

# --- Configuration for Conference Details ---
CONFERENCES = {
    "Zodopt Summit 2025": {
        "date": "October 10-12, 2025",
        "location": "San Francisco, CA",
        "price": 1299,
        "description": "Our flagship annual summit covering the future of AI, cloud infrastructure, and sustainable technology. Featuring keynote speakers from global tech leaders."
    },
    "Meetease Developer Workshop": {
        "date": "December 5, 2024",
        "location": "Virtual Event",
        "price": 499,
        "description": "A focused, one-day workshop for developers diving deep into our new API stack, security protocols, and advanced deployment strategies."
    }
}


def conference_main(request, navigate_to):
    """
    Renders the Conference Booking page for the Streamlit application.
    
    Args:
        request (dict): The current request context dictionary (e.g., {'path': '/conference'}).
        navigate_to (function): A function used for internal navigation (e.g., navigate_to('home')).
    """

    # --- Custom CSS for Styling ---
    st.markdown("""
    <style>
    /* Styling for the entire page container */
    .stApp {
        padding-top: 20px;
    }

    /* Container for the main form/card */
    .conference-card {
        background: #f7f9fb;
        padding: 40px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        margin-top: 30px;
    }

    /* Style for conference selection box */
    .stSelectbox div[data-baseweb="select"] {
        border-radius: 10px;
        border: 2px solid #ccc;
        padding: 5px;
    }

    /* Match button style from main.py */
    .stButton button {
        background-color: #1e62ff !important;
        color: white !important;
        border: none !important;
        border-radius: 0.5rem !important;  
        transition: all 0.3s ease;
        font-weight: 600;
        padding: 10px 20px;
    }
    
    .stButton button:hover {
        background-color: #8a2eff !important;
        box-shadow: 0 4px 12px rgba(138, 46, 255, 0.4);
    }

    .stAlert {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.header("📘 Conference Booking")
    st.markdown(f"**Current Request Path:** `{request.get('path', '/')}`", unsafe_allow_html=True)
    st.write("Secure your spot for upcoming Zodopt events and world-class industry summits.")

    # --- Main Booking Form ---
    st.markdown('<div class="conference-card">', unsafe_allow_html=True)

    # 1. Conference Selection
    conference_names = list(CONFERENCES.keys())
    selected_name = st.selectbox(
        "Select Conference to Book",
        conference_names,
        key="selected_conf"
    )

    if selected_name:
        conf_details = CONFERENCES[selected_name]
        
        st.subheader(selected_name)
        
        col_info, col_desc = st.columns([1, 2])
        
        with col_info:
            st.metric(label="Date", value=conf_details['date'], delta="Upcoming")
            st.metric(label="Location", value=conf_details['location'])
            st.metric(label="Registration Fee", value=f"${conf_details['price']:,}")

        with col_desc:
            st.info(f"**Description:** {conf_details['description']}")
            
        st.markdown("---")
        
        # 2. Registration Form Details
        st.markdown("##### Attendee Details")
        
        col_name, col_email = st.columns(2)
        with col_name:
            name = st.text_input("Full Name", key="attendee_name")
        with col_email:
            email = st.text_input("Email Address", key="attendee_email")
            
        # 3. Booking Confirmation
        num_tickets = st.number_input(
            "Number of Tickets", 
            min_value=1, 
            max_value=10, 
            value=1, 
            key="num_tickets_conf"
        )
        
        total_price = num_tickets * conf_details['price']
        
        st.success(f"**Total Cost:** ${total_price:,}")

        st.checkbox("I agree to the terms and conditions.", key="terms_agreed")

        # 4. Action Button
        if st.button(f"Proceed to Payment for {selected_name}", use_container_width=True):
            if not name or not email:
                st.error("Please fill in your name and email address.")
            elif not st.session_state.terms_agreed:
                st.error("You must agree to the terms and conditions to proceed.")
            else:
                st.balloons()
                st.session_state.booking_status = {
                    "conf": selected_name,
                    "name": name,
                    "email": email,
                    "tickets": num_tickets,
                    "cost": total_price,
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.success(f"✅ Booking successful for **{selected_name}**! Check your email at {email} for details.")
                # Clear form fields for next use
                st.session_state.attendee_name = ""
                st.session_state.attendee_email = ""
                st.session_state.terms_agreed = False
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation button back to home
    if st.button("← Back to Home"):
        navigate_to("home")
