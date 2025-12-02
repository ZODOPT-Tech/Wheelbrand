import streamlit as st

# ---------------------------------------------------------
# Custom CSS (Replicated from the original design)
# ---------------------------------------------------------
def load_css():
    """Injects custom CSS for branding and layout aesthetics."""
    st.markdown("""
    <style>
    /* General Container adjustments */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        max-width: 1500px !important;
    }
    
    /* Ensure the Streamlit 'app-container' is wide */
    .stApp {
        background-color: #f0f2f5; 
        font-family: 'Inter', sans-serif;
    }

    /* HEADER BAR */
    .header-bar {
        width: 100%;
        background: linear-gradient(90deg, #2356F6, #5A38F9, #8A23FF);
        padding: 45px 70px;
        border-radius: 35px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 60px;
        box-shadow: 0 10px 30px rgba(35, 86, 246, 0.3);
    }

    .header-title {
        font-size: 42px;
        font-weight: 800;
        color: white;
        letter-spacing: 1px;
    }

    /* ZODOPT LOGO IMAGE (Adjusted for Streamlit's image handling or placeholder) */
    .logo-img {
        height: 60px;
        width: 160px; /* Explicit width for consistent layout */
        object-fit: contain;
        border-radius: 8px;
    }

    /* CARDS */
    .option-card {
        background: white;
        border-radius: 22px;
        padding: 25px;
        height: 420px;
        text-align: center;
        box-shadow: 0px 8px 28px rgba(0,0,0,0.08);
        position: relative;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
        transition: transform 0.2s;
    }
    
    .option-card:hover {
        transform: translateY(-5px);
        box-shadow: 0px 15px 35px rgba(0,0,0,0.1);
    }


    .icon-circle {
        width: 200px;
        height: 200px;
        border-radius: 50%;
        margin: 45px auto 30px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 95px;
        color: white;
    }

    .calendar-icon {
        background: linear-gradient(45deg, #5A4BFF, #A53CFF);
    }

    .book-icon {
        background: #00a884;
    }
    
    /* Target Streamlit button structure */
    .stButton>button {
        width: 100%;
        min-height: 58px; /* Added min-height */
        background: #1A5CFF !important;
        color: white !important;
        border: none !important;
        padding: 18px 0 !important;
        border-radius: 12px !important;
        font-size: 20px !important;
        font-weight: 600 !important;
        margin-top: auto; /* Push button to bottom of flex container */
        box-shadow: 0 4px 10px rgba(26, 92, 255, 0.4);
        transition: background 0.2s;
    }

    .stButton>button:hover {
        background: #004de6 !important;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .header-bar {
            padding: 30px 20px;
            border-radius: 20px;
            margin-bottom: 30px;
        }
        .header-title {
            font-size: 28px;
        }
        .logo-img {
            height: 40px;
        }
        .option-card {
            height: auto; /* Allow height to adjust on mobile */
        }
        .icon-circle {
            width: 150px;
            height: 150px;
            font-size: 70px;
            margin: 20px auto;
        }
    }

    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# PAGE FUNCTIONS
# ---------------------------------------------------------

def render_main_screen():
    """Renders the dashboard with card options."""
    
    # ------------------ HEADER BAR -----------------------
    # Use HTML/CSS to manage the whole bar layout
    st.markdown('<div class="header-bar">', unsafe_allow_html=True)
    
    # Title (Left)
    st.markdown('<div class="header-title">ZODOPT MEETEASE</div>', unsafe_allow_html=True)

    # Logo (Right - using a placeholder for the image source)
    st.markdown("""
        <img src="https://placehold.co/160x60/ffffff/000000?text=ZODOPT+Logo" 
             class="logo-img" 
             alt="ZODOPT Logo">
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ------------------ CARD SECTION ----------------------
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<div class="option-card">', unsafe_allow_html=True)
        st.markdown('<div class="icon-circle calendar-icon">📅</div>', unsafe_allow_html=True)
        st.markdown('<h2 class="text-3xl font-semibold text-gray-800 mb-6">Visitor Plan</h2>', unsafe_allow_html=True)
        
        # Streamlit button needs to be outside the custom div closure to function correctly
        if st.button("Proceed to Visit Planning", key="btn_visit_plan"):
            st.session_state.current_page = "visitor_login"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True) # End option-card

    with col2:
        st.markdown('<div class="option-card">', unsafe_allow_html=True)
        st.markdown('<div class="icon-circle book-icon">📚</div>', unsafe_allow_html=True)
        st.markdown('<h2 class="text-3xl font-semibold text-gray-800 mb-6">Conference Booking</h2>', unsafe_allow_html=True)

        if st.button("Proceed to Conference Booking", key="btn_conference_booking"):
            st.session_state.current_page = "conference_login"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True) # End option-card

    st.markdown('<p class="text-center text-gray-500 mt-10 text-sm">A ZODOPT Visitor and Conference Management System.</p>', unsafe_allow_html=True)

def render_visitor_login():
    """Renders the Visitor Login screen."""
    st.title("Visitor Login")
    st.subheader("Manage Your Visit Plan")

    with st.container(border=True):
        st.markdown("Please enter your credentials to manage your visit plan.")
        
        # Input fields
        email = st.text_input("Email Address", key="visitor_email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", key="visitor_password")

        st.markdown('<style>.stTextInput label {display: none;}</style>', unsafe_allow_html=True)

        if st.button("Log In", key="visitor_login_btn", help="Click to log in"):
            # Placeholder for actual login logic
            if email and password:
                st.success(f"Attempting to log in as {email}...")
                # Here you would typically perform authentication and then navigate
            else:
                st.error("Please enter both email and password.")

    if st.button("← Back to Main", key="back_to_main_visitor"):
        st.session_state.current_page = "main"
        st.rerun()

def render_conference_login():
    """Renders the Conference Admin Login screen."""
    st.title("Conference Admin Login")
    st.subheader("Staff Sign-in")

    with st.container(border=True):
        st.markdown("Staff sign-in to manage conference schedules.")
        
        # Input fields
        staff_id = st.text_input("Staff ID", key="staff_id", placeholder="Staff ID")
        passcode = st.text_input("Passcode", type="password", key="staff_passcode")
        
        st.markdown('<style>.stTextInput label {display: none;}</style>', unsafe_allow_html=True)
        
        # Custom button styling for conference login (green/teal)
        st.markdown("""
        <style>
        #conference_login_btn > button {
            background: #00a884 !important;
            box-shadow: 0 4px 10px rgba(0, 168, 132, 0.4);
        }
        #conference_login_btn > button:hover {
            background: #008f73 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        if st.button("Secure Access", key="conference_login_btn", help="Click to access admin panel"):
            # Placeholder for actual login logic
            if staff_id and passcode:
                st.success(f"Verifying access for Staff ID: {staff_id}...")
                # Here you would typically perform authentication and then navigate
            else:
                st.error("Please enter both Staff ID and Passcode.")

    if st.button("← Back to Main", key="back_to_main_conference"):
        st.session_state.current_page = "main"
        st.rerun()

# ---------------------------------------------------------
# MAIN APP EXECUTION
# ---------------------------------------------------------
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    load_css()
    
    # Initialize session state for page navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "main"

    # Route logic
    if st.session_state.current_page == "main":
        render_main_screen()
    elif st.session_state.current_page == "visitor_login":
        render_visitor_login()
    elif st.session_state.current_page == "conference_login":
        render_conference_login()
