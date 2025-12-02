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
            margin-bottom: 40px; /* Increased margin for better separation */
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
            /* Styling for "zodopt" text colors */
            color: white;
        }
        .logo-placeholder span.z { color: #cc0000; } 
        .logo-placeholder span.o { color: #ff9900; }
        .logo-placeholder span.d { color: #66cc33; }
        .logo-placeholder span.p { color: #0099cc; }
        .logo-placeholder span.t { color: #ff6699; }

        /* Card Styling */
        .stContainer {
            /* Make the card boundary match the image's clean, borderless look */
            border: 1px solid #f0f0f0; 
            background-color: white;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); /* Stronger shadow */
            height: 380px; /* Fixed height for visual consistency */
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        
        /* Icon Placeholder Styling (Simulated Icons) */
        .icon-box-calendar {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: linear-gradient(45deg, #7c4dff, #b388ff); /* Purple/Calendar Icon Color */
            margin: 40px auto; /* Centered, larger margin for vertical spacing */
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 60px;
            color: white;
        }

        .icon-box-book {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: #00a884; /* Deep Emerald Green/Book Icon Color */
            margin: 40px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 60px;
            color: white;
        }
        
        /* Button Styling (Full width and blue) */
        .stButton>button {
            width: 100%;
            background-color: #2196F3; /* Bright Blue */
            color: white;
            border: none;
            padding: 15px; /* Bigger button */
            border-radius: 0 0 15px 15px; /* Rounded only at the bottom to fuse with card */
            font-weight: bold;
            font-size: 18px;
            margin: 0; /* Remove default margin */
            position: absolute;
            bottom: 0;
            left: 0;
            cursor: pointer;
        }
        .stButton>button:hover {
             background-color: #1976D2;
        }
        
        /* Ensure the container is ready for absolute positioning */
        [data-testid="stVerticalBlock"] > div > div > [data-testid="stVerticalBlock"] {
             position: relative;
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
                <span class="logo-placeholder">z<span class="o">o</span>d<span class="o">o</span>p<span class="t">t</span></span>
            </div>
            """, 
            unsafe_allow_html=True
        )

    # 3. Main Content Columns
    col1, col2 = st.columns(2)

    # --- VISITOR CARD (Left) ---
    with col1:
        # Use a container to simulate the card look
        with st.container(border=False):
            # ICON Placeholder (Calendar Icon)
            st.markdown('<div class="icon-box-calendar">📅</div>', unsafe_allow_html=True)
            
            # Button labeled "Visit Plan"
            if st.button("Visit Plan", key="main_visitor"):
                st.session_state['current_page'] = 'visitor_login'
                st.rerun()

    # --- CONFERENCE CARD (Right) ---
    with col2:
        # Use a container to simulate the card look
        with st.container(border=False):
            # ICON Placeholder (Book Icon)
            st.markdown('<div class="icon-box-book">📚</div>', unsafe_allow_html=True)
            
            # Button labeled "Conference Booking"
            if st.button("Conference Booking", key="main_conference"):
                st.session_state['current_page'] = 'conference_login'
                st.rerun()

    # Remove the bottom line and caption for a cleaner look, closer to the image
    # st.markdown("---")
     st.caption("A ZODOPT Visitor and Conference Management System.")
