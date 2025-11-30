import streamlit as st
import os
import base64

# --- Configuration ---
LOGO_PATH = r"zodopt.png"
LOGO_PLACEHOLDER_TEXT = "zodopt"
HEADER_GRADIENT = "linear-gradient(90deg, #50309D, #7A42FF)" # Primary Color

# Utility function to convert image to base64 for embedding
def _get_image_base64(path):
    """Converts a local image file to a base64 string for embedding in HTML/CSS."""
    try:
        # NOTE: Since the file 'zodopt.png' likely doesn't exist in the execution environment, 
        # this will default to returning an empty string, which the rendering handles.
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except Exception:
        return ""

def render_main_screen():
    
    # 1. Inject Custom CSS 🎨
    st.markdown(f"""
    <style>
    /* Global Streamlit Overrides */
    html, body {{
        margin-top: 0 !important;
        padding-top: 0 !important;
        overflow-x: hidden; /* Prevent horizontal scrollbar */
        font-family: 'Segoe UI', sans-serif;
    }}
    .stApp .main {{
        padding-top: 0px !important; 
        margin-top: 0px !important;
    }}
    .stApp > header {{ visibility: hidden; }}
    
    /* CRITICAL CHANGE: Remove all default padding/max-width from Streamlit's main content block (block-container) 
       to allow the header to span truly edge-to-edge. */
    .stApp .main .block-container {{
        padding-top: 0 !important;
        padding-right: 0 !important;
        padding-left: 0 !important;
        padding-bottom: 2rem !important; 
        max-width: 100% !important; 
    }}

    /* Header Box (Now truly full width) */
    .header-box {{
        background: {HEADER_GRADIENT};
        padding: 20px 40px; 
        margin-top: 0px; 
        margin-bottom: 40px;
        border-radius: 0; /* Ensures full edge-to-edge fit */
        box-shadow: 0 4px 15px rgba(0,0,0,0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%; /* Spans the full width of the now-unpadded block-container */
        margin-left: 0;
        margin-right: 0;
    }}
    
    .header-title {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
        font-size: 34px;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: 1.5px;
        margin: 0;
    }}

    /* NEW: Wrapper for content below the header to re-add necessary padding and centering */
    .content-wrapper {{
        padding-top: 1.5rem;
        padding-right: 2rem;
        padding-left: 2rem;
        max-width: 1200px; /* Optional: Re-sets a max width for content on large monitors */
        margin: 0 auto; /* Center the content wrapper */
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
        min-height: 250px;
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

    /* Streamlit Button Style (Matching Header Color) */
    .stButton > button {{
        background: {HEADER_GRADIENT} !important; /* MATCH HEADER GRADIENT */
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 15px 20px !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 10px rgba(80, 48, 157, 0.4) !important; /* Shadow using main color */
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


    # 2. HEADER (Logo Inside Container) 🖼️
    
    if os.path.exists(LOGO_PATH):
        logo_html = f'<img src="data:image/png;base64,{_get_image_base64(LOGO_PATH)}" class="header-logo-img" style="height: 50px; border-radius: 8px;">'
    else:
        logo_html = f'<div class="header-logo-container">**{LOGO_PLACEHOLDER_TEXT}**</div>'

    # The header is rendered first, spanning full width due to CSS changes on .block-container
    st.markdown(
        f"""
        <div class="header-box">
            <div class="header-title">ZODOPT MEETEASE</div> 
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 3. Start Content Wrapper (Applies padding/max-width to everything below the header)
    st.markdown(
        """<div class="content-wrapper">""",
        unsafe_allow_html=True
    )

    # 4. CARDS and BUTTONS
    
    st.markdown('<div style="margin-top: 1.5rem;"></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)

    # --- Visit Plan Card and Button ---
    with col1:
        st.markdown(
            """
            <div class="dashboard-card-container">
                <div class="new-icon-circle visitplan-icon-gradient">
                    <svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-calendar"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("VISITPLAN", key="visit_plan_btn", use_container_width=True):
            st.session_state['current_page'] = 'visitor_login'
            # st.rerun() # Commented out for environment compatibility

    # --- Conference Booking Card and Button ---
    with col2:
        st.markdown(
            """
            <div class="dashboard-card-container">
                <div class="new-icon-circle conference-icon-gradient">
                    <svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-book-open"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("CONFERENCE BOOKING", key="conference_booking_btn", use_container_width=True):
            st.session_state['current_page'] = 'conference_login'
            # st.rerun() # Commented out for environment compatibility

    # 5. End Content Wrapper
    st.markdown(
        """</div>""",
        unsafe_allow_html=True
    )
    
