import streamlit as st

# --- Custom CSS for Styling ---
# Define CSS for the header and the selection cards to match the image's aesthetic
def custom_css():
    st.html("""
        <style>
        /* Header Bar Styling */
        .main-header {
            background: linear-gradient(90deg, #5333e6, #7a50ff); /* Blue/Purple Gradient */
            padding: 10px 20px;
            border-radius: 10px;
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .main-header h1 {
            color: white;
            font-size: 28px;
            margin: 0;
            flex-grow: 1;
        }
        
        /* Zodopt Logo Text/Image Placeholder (Simulated) */
        .logo-placeholder {
            font-size: 24px;
            font-weight: bold;
            color: #ee55aa; /* Bright color for "zodopt" */
        }

        /* Card Styling */
        .stContainer {
            border: 1px solid #e0e0e0;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            height: 100%; /* Important for equal height columns */
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        
        /* Icon Placeholder Styling (Simulated Icons) */
        .icon-box-calendar {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: linear-gradient(45deg, #7c4dff, #b388ff); /* Purple/Calendar Icon Color */
            margin: 0 auto 20px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            color: white;
        }

        .icon-box-book {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: #2ecc71; /* Green/Book Icon Color */
            margin: 0 auto 20px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            color: white;
        }
        
        /* Button Styling (Full width and blue) */
        .stButton>button {
            width: 100%;
            background-color: #2196F3; /* Bright Blue */
            color: white;
            border: none;
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            margin-top: auto; /* Push button to the bottom */
        }
        .stButton>button:hover {
             background-color: #1976D2;
        }
        </style>
    """)

# --- Main Rendering Function ---

def render_main_screen():
    # 1. Apply Custom CSS
    custom_css()

    # 2. Render Custom Header (Matches the banner in the image)
    with st.container():
        st.markdown(
            f"""
            <div class="main-header">
                <h1>ZODOPT MEETEASE</h1>
                <span class="logo-placeholder">zodopt</span>
            </div>
            """, 
            unsafe_allow_html=True
        )

    # 3. Main Content Columns
    col1, col2 = st.columns(2)

    # --- VISITOR CARD (Left) ---
    with col1:
        # Use a container to simulate the card look
        with st.container(border=True):
            # ICON Placeholder
            st.markdown('<div class="icon-box-calendar">🗓️</div>', unsafe_allow_html=True)
            
            # Text based on the image (Visit Plan) but triggering Visitor flow
            st.subheader("Visit Plan")
            st.caption("Plan your visit, check adoption status, and manage identity documents.")

            if st.button("Visitor Login / Sign Up", key="main_visitor"):
                st.session_state['current_page'] = 'visitor_login'
                st.rerun()

    # --- CONFERENCE CARD (Right) ---
    with col2:
        # Use a container to simulate the card look
        with st.container(border=True):
            # ICON Placeholder
            st.markdown('<div class="icon-box-book">📘</div>', unsafe_allow_html=True)
            
            # Text based on the image (Conference Booking)
            st.subheader("Conference Booking")
            st.caption("Access management tools for authorized personnel bookings.")

            if st.button("Conference Login", key="main_conference"):
                st.session_state['current_page'] = 'conference_login'
                st.rerun()

    st.markdown("---")
    st.caption("A ZODOPT Visitor and Conference Management System.")

# Note: You should place the 'zodopt.png' logo file in the same directory as your main app.
# The current code uses a CSS text placeholder for the logo, as Streamlit's image function 
# doesn't fit neatly into the HTML-styled header bar without more complex positioning. 
# You can replace the 'zodopt' text span with an actual image tag if needed.
