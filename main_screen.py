
import streamlit as st
import os
import base64

# --- Configuration ---
# Assuming these constants are defined globally or passed via session state
# If this file is imported by app.py, these keys must match those in app.py
PAGE_V_LOGIN = 'visitor_login'
PAGE_C_LOGIN = 'conference_login'

LOGO_PATH = r"zodopt.png"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)" # Primary Color

# --- Navigation Helper ---
# Abstracted navigation logic for cleaner event handling
def navigate_to(page_key: str):
    """Updates the session state to change the currently rendered page."""
    st.session_state['current_page'] = page_key
    st.rerun()

# Utility function to convert image to base64 for embedding
def _get_image_base64(path):
    """Converts a local image file to a base64 string for embedding in HTML/CSS."""
    # In a real environment, this would read the file.
    # Since the file is not available here, we'll return an empty string.
    try:
        if os.path.exists(path):
            with open(path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
        # Fallback placeholder data (a small purple square)
        return "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDTAgAQJUYAKYfBpZZXFw5AAAAAElFTkSuQmCC"
    except Exception:
        return ""

def render_main_screen():
    
    # Define a consistent horizontal padding for content inside the full-width layout
    APP_PADDING_X = "2rem" 
    
    # 1. Inject Custom CSS 🎨
    # NOTE: The global overrides for .stApp .main .block-container should ideally be 
    # injected once in the main app.py, but are included here for modularity.
    st.markdown(f"""
    <style>
    /* Global Streamlit Overrides */
    .stApp .main {{
        padding-top: 0px !important; 
        margin-top: 0px !important;
    }}
    .stApp > header {{ visibility: hidden; }}
    
    /* CRITICAL: Overrides to force full screen width and remove default margins/padding */
    .stApp .main .block-container, 
    .css-18e3th9, 
    .css-1rq2lgs {{ 
        padding: 0 !important;
        max-width: 100% !important; 
        margin: 0 !important;
    }}
    
    /* Header Box */
    .header-box {{
        background: {HEADER_GRADIENT};
        padding: 20px {APP_PADDING_X}; 
        margin-top: 0px; 
        margin-bottom: 40px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        margin: 0;
    }}
    
    .header-title {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
        font-size: 34px;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: 1.5px;
        margin: 0;
    }}

    /* Card container styling */
    .dashboard-card-container {{
        background: white;
        border-radius: 12px;
        padding: 30px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        min-height: 280px; /* Slightly increased height to accommodate text */
        margin-bottom: 20px;
    }}

    /* Icon styling */
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

    /* FIX: Streamlit Button Style */
    .stButton > button {{
        background: {HEADER_GRADIENT} !important; 
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
    logo_html = f'<img src="data:image/png;base64,{_get_image_base64(LOGO_PATH)}" class="header-logo-img" style="height: 50px; border-radius: 8px;">'

    st.markdown(
        f"""
        <div class="header-box">
            <div class="header-title">ZODOPT MEETEASE</div> 
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3. CARDS and BUTTONS
    # Use a Streamlit container to manage the main content area padding
    with st.container():
        # Apply padding via CSS in a markdown block for the container
        st.markdown(f'<div style="padding: 0 {APP_PADDING_X}; margin-top: 1.5rem;">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)

        # --- Visit Plan Card and Button ---
        with col1:
            st.markdown(
                """
                <div class="dashboard-card-container">
                    <div class="new-icon-circle visitplan-icon-gradient">
                        <!-- Feather icon for Calendar/Visit -->
                        <svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-calendar"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                    </div>
                    <div class="card-title">Plan Your Visit</div>
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
                        <!-- Feather icon for Conference/Booking -->
                        <svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-briefcase"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
                    </div>
                    <div class="card-title">Manage Conferences</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            # Use the abstracted navigate_to function
            if st.button("CONFERENCE ADMIN", key="conference_booking_btn", use_container_width=True):
                navigate_to(PAGE_C_LOGIN)
                
        # Close the content wrapper div
        st.markdown('</div>', unsafe_allow_html=True)

# NOTE: The execution guard below is removed as this file is intended to be imported as a module.
# The main application logic resides in app.py.
