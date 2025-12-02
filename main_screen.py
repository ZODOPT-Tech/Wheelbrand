import streamlit as st
from PIL import Image # Needed if you want to use PIL for logo manipulation (optional)

# --- Configuration ---
# NOTE: Assume 'zodopt.png' is in the same directory as the script.
# If you don't have the image, the code will still run, but the logo won't show.
LOGO_PATH = "zodopt.png"

# --- Styling and UI Functions ---

def load_custom_css():
    """Injects custom CSS for the banner and cards."""
    st.markdown("""
        <style>
            /* Custom CSS for the Zodopt Meetease Banner */
            .zodopt-banner {
                background: linear-gradient(to right, #4A00E0, #8E2DE2); /* Gradient from the image */
                padding: 10px 20px;
                border-radius: 10px;
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
            }
            .zodopt-banner h1 {
                margin: 0;
                font-size: 24px;
                font-weight: 700;
            }
            .zodopt-logo-text {
                font-size: 30px;
                font-weight: 800;
                color: #ff5733; /* Use a placeholder color or fetch the correct 'zodopt' color */
                /* For a real image logo, you'd use a different approach (see below) */
            }

            /* Custom CSS for the Action Cards */
            .action-card {
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                padding: 20px;
                height: 300px; /* Fixed height for consistency */
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
                justify-content: space-between;
                cursor: pointer;
                transition: transform 0.2s;
            }
            .action-card:hover {
                transform: translateY(-5px);
            }
            .card-icon-container {
                width: 120px;
                height: 120px;
                border-radius: 50%;
                margin-bottom: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            /* Specific icon colors from the image */
            .visit-plan-icon {
                background: radial-gradient(circle, #D295FF, #8E2DE2); /* Purple gradient */
            }
            .conference-icon {
                background: radial-gradient(circle, #7DFF9E, #00A651); /* Green gradient */
            }
            /* Styling the buttons to look like the image's bottom banner */
            .stButton>button {
                width: 100%;
                margin-top: 10px;
                padding: 10px 0;
                font-weight: bold;
                border: none;
                border-radius: 0 0 10px 10px; /* Rounded only at the bottom if using a parent container */
            }
            /* Override for button colors */
            .visit-plan-button button {
                background-color: #4A00E0; /* Darker purple */
                color: white;
                border-radius: 0 0 10px 10px;
            }
            .conference-button button {
                background-color: #00A651; /* Darker green */
                color: white;
                border-radius: 0 0 10px 10px;
            }
            /* Icon styling (using Streamlit's default emoji support) */
            .card-icon-container h1 {
                font-size: 60px;
                margin: 0;
            }
        </style>
    """, unsafe_allow_html=True)


def render_main_screen():
    """Renders the main selection screen based on the provided image."""
    
    # Load custom CSS
    load_custom_css()

    # 1. ZODOPT MEETEASE Banner with Logo (Top Section)
    
    # Try to load the image if available for the right side of the banner
    try:
        # Load the logo image and resize it for the banner if needed
        logo_img = Image.open(LOGO_PATH)
        st_logo = logo_img.resize((100, 30)) # Adjust size as needed
        # Use columns to align the text and the logo image
        col_banner_left, col_banner_right = st.columns([0.8, 0.2])
        
        with col_banner_left:
             # Injecting the banner with HTML for full control
            st.markdown(
                """
                <div class="zodopt-banner">
                    <h1>ZODOPT MEETEASE</h1>
                </div>
                """, unsafe_allow_html=True
            )
        
        # This part is tricky in Streamlit. Instead of a single banner div,
        # we'll use a hack to make the text and image appear side-by-side
        # within the overall gradient look.
        # A simpler approach is to use pure HTML for the whole banner:
        st.markdown(
            f"""
            <div class="zodopt-banner">
                <h1>ZODOPT MEETEASE</h1>
                <img src="{LOGO_PATH}" width="80" style="filter: brightness(0) invert(1) drop-shadow(0 0 5px rgba(255, 255, 255, 0.5));">
            </div>
            """, unsafe_allow_html=True
        )

    except FileNotFoundError:
        # Fallback if the logo image is not present
        st.markdown(
            """
            <div class="zodopt-banner">
                <h1>ZODOPT MEETEASE</h1>
                <span class="zodopt-logo-text" style="color: white; font-size: 30px;">ZODOPT</span>
            </div>
            """, unsafe_allow_html=True
        )


    # 2. Action Cards (Middle Section)
    
    st.markdown("##") # Add some vertical space

    col1, col2 = st.columns(2)

    # --- Card 1: Visit Plan ---
    with col1:
        st.markdown(
            """
            <div class="action-card" onclick="alert('Visit Plan Clicked');">
                <div class="card-icon-container visit-plan-icon">
                    <h1>📅</h1> </div>
            </div>
            """, unsafe_allow_html=True
        )
        # The button is placed separately below the HTML card component
        # The key is to make the button look like the bottom part of the card
        st.markdown('<div class="visit-plan-button">', unsafe_allow_html=True)
        if st.button("Visit Plan", key="card_visit_plan"):
            # Update state for navigation
            st.session_state['current_page'] = 'visit_plan'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


    # --- Card 2: Conference Booking ---
    with col2:
        st.markdown(
            """
            <div class="action-card" onclick="alert('Conference Booking Clicked');">
                <div class="card-icon-container conference-icon">
                    <h1>📘</h1> </div>
            </div>
            """, unsafe_allow_html=True
        )
        # The button is placed separately below the HTML card component
        st.markdown('<div class="conference-button">', unsafe_allow_html=True)
        if st.button("Conference Booking", key="card_conference_booking"):
            # Update state for navigation
            st.session_state['current_page'] = 'conference_booking'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# --- Example of running the function (for testing) ---

# if 'current_page' not in st.session_state:
#     st.session_state['current_page'] = 'main'

# if st.session_state['current_page'] == 'main':
#     render_main_screen()
# else:
#     st.write(f"Navigated to: {st.session_state['current_page']}")
#     if st.button("Back to Main"):
#         st.session_state['current_page'] = 'main'
#         st.rerun()
