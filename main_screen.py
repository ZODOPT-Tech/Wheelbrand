import streamlit as st
import os
import base64
from typing import Callable

# --- Configuration ---
# Assuming these constants are defined globally or passed via session state
# If this file is imported by app.py, these keys must match those in app.py
PAGE_V_LOGIN = 'visitor_login'
PAGE_C_LOGIN = 'conference_login'

LOGO_PATH = r"zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)" # Primary Color
APP_PADDING_X = "2rem" # Consistent horizontal padding

# --- Navigation Helper ---
# Abstracted navigation logic for cleaner event handling
# This function should be passed from the main application (app.py)
# Note: For this module to work in isolation, we'll define a simple one,
# but the calling module must pass its own via the render_main_screen argument.
def _default_navigate_to(page_key: str):
     st.session_state['current_page'] = page_key
     st.rerun()

# Utility function to convert image to base64 for embedding
def _get_image_base64(path: str) -> str:
    """Converts a local image file to a base64 string for embedding in HTML/CSS."""
    try:
        # Check if the file exists and is readable
        if os.path.exists(path) and os.path.getsize(path) > 0:
            with open(path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
        
        # Fallback placeholder data (a small purple square)
        # This prevents errors if the file is missing during development
        return "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDTAgAQJUYAKYfBpZZXFw5AAAAAElFTkSuQmCC"
    except Exception:
        # Handle exceptions gracefully
        return ""

def render_main_screen(navigate_to: Callable[[str], None] = _default_navigate_to):
    """
    Renders the main landing page with two navigation cards for Visitor and Conference Admin.

    Args:
        navigate_to: The navigation function provided by the main app router.
    """
    
    # Pre-calculate base64 string for cleaner CSS injection
    logo_b64 = _get_image_base64(LOGO_PATH)
    
    # 1. Inject Custom CSS 🎨
    st.markdown(f"""
    <style>
    /* -------------------------------------- */
    /* GLOBAL OVERRIDES (App-wide scope) */
    /* -------------------------------------- */
    .stApp > header {{ visibility: hidden; }} /* Hides the default Streamlit header */
    
    /* CRITICAL: Overrides to force full screen width and remove default margins/padding */
    /* This ensures content starts at the very top-left */
    .stApp .main,
    .stApp .main .block-container, 
    .css-18e3th9, /* block-container selector */
    .css-1rq2lgs {{ /* block-container padding removal */
        padding: 0 !important;
        max-width: 100% !important; 
        margin: 0 !important;
        padding-top: 0px !important; 
        margin-top: 0px !important;
    }}
    
    /* CSS Variables for use throughout the component */
    :root {{
        --header-gradient: {HEADER_GRADIENT};
        --primary-color: #50309D;
        --secondary-color: #7A42FF;
        --app-padding-x: {APP_PADDING_X};
        --logo-b64: url('data:image/png;base64,{logo_b64}');
    }}

    /* -------------------------------------- */
    /* HEADER STYLES */
    /* -------------------------------------- */
    .header-box {{
        background: var(--header-gradient);
        padding: 20px var(--app-padding-x); 
        box-shadow: 0 4px 15px rgba(0,0,0,0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        margin-bottom: 30px; /* Space below the header */
    }}
    
    .header-title {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
        font-size: 34px;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: 1.5px;
        margin: 0;
    }}
    
    .header-logo-img {{
        height: 50px; 
        width: 50px; /* Ensure square aspect ratio */
        border-radius: 8px;
        background-image: var(--logo-b64); /* Use CSS variable */
        background-size: cover;
        background-position: center;
    }}

    /* -------------------------------------- */
    /* CARD STYLES */
    /* -------------------------------------- */
    .dashboard-card-container {{
        background: white;
        border-radius: 12px;
        padding: 30px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        min-height: 280px; 
        margin-bottom: 20px;
    }}

    .new-icon-circle {{
        width: 120px;
        height: 120px;
        border-radius: 50%;
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    }}
    .visitplan-icon-gradient {{
        background: linear-gradient(135deg, #a464ff, #4711f7); /* Purple gradient */
    }}
    .conference-icon-gradient {{
        background: linear-gradient(135deg, #10b48a, #0d7056); /* Green gradient */
    }}
    
    .card-title {{
        font-size: 24px;
        font-weight: 700;
        color: #333;
        margin-bottom: 10px;
    }}
    .card-description {{
        font-size: 16px;
        color: #666;
        margin-bottom: 20px;
    }}

    /* -------------------------------------- */
    /* STREAMLIT BUTTON OVERRIDES */
    /* -------------------------------------- */
    .stButton > button {{
        background: var(--header-gradient) !important; 
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 15px 20px !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 10px rgba(80, 48, 157, 0.4) !important; 
        width: 100% !important;
        margin-top: 15px;
        transition: all 0.2s ease-in-out;
    }}
    .stButton > button:hover {{
        opacity: 0.9;
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(80, 48, 157, 0.6) !important;
    }}
    </style>
    """, unsafe_allow_html=True)


    # 2. HEADER 🖼️
    # Use the CSS variable for the logo, keep minimal HTML for structure
    st.markdown(
        """
        <div class="header-box">
            <div class="header-title">ZODOPT MEETEASE</div> 
            <div class="header-logo-img"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3. CARDS and BUTTONS
    # Use a simple div for main content padding
    st.markdown(f'<div style="padding: 0 {APP_PADDING_X}; margin-top: 1.5rem;">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)

    # --- Visit Plan Card and Button ---
    with col1:
        st.markdown(
            """
            <div class="dashboard-card-container">
                <div class="new-icon-circle visitplan-icon-gradient">
                    <svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-calendar"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                </div>
                <div class="card-title">Plan Your Visit</div>
                <div class="card-description">
                    Check-in for your pre-booked visit, verify your identity, and view your schedule.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        # Use the abstracted navigate_to function
        if st.button("VISIT CHECK-IN", key="visit_plan_btn", use_container_width=True):
            navigate_to(PAGE_V_LOGIN)

    # --- Conference Booking Card and Button ---
    with col2:
        st.markdown(
            """
            <div class="dashboard-card-container">
                <div class="new-icon-circle conference-icon-gradient">
                    <svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-briefcase"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
                </div>
                <div class="card-title">Manage Conferences</div>
                <div class="card-description">
                    Login as an administrator to manage room bookings and view staff schedules.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        # Use the abstracted navigate_to function
        if st.button("CONFERENCE ADMIN", key="conference_booking_btn", use_container_width=True):
            navigate_to(PAGE_C_LOGIN)
            
    # Close the content wrapper div
    st.markdown('</div>', unsafe_allow_html=True)
