import streamlit as st

# --- Configuration for Styling ---
# Define colors based on the image provided
VISITPLAN_COLOR_START = "#6b21a8" # Deeper Purple
VISITPLAN_COLOR_END = "#a855f7"   # Lighter Purple
CONFERENCE_COLOR_START = "#059669" # Deeper Green
CONFERENCE_COLOR_END = "#34d399"   # Lighter Green

def nav_card(title, icon, page_path, color_start, color_end, key):
    """Generates a styled, clickable card for navigation."""
    
    # Custom CSS for the card container and hover effect
    card_css = f"""
    <style>
    .card-{{key}} {{
        background-color: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        text-align: center;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        /* Increased height to match the vertical spacing in the image */
        margin-bottom: 20px;
        height: 250px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }}
    .card-{{key}}:hover {{
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
    }}
    .icon-container-{{key}} {{
        width: 80px;
        height: 80px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 30px;
        color: white;
        background-image: linear-gradient(135deg, {color_start} 0%, {color_end} 100%);
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }}
    .card-title-{{key}} {{
        font-size: 1.5rem;
        font-weight: 600;
        color: #1f2937; /* Dark text, matching image aesthetics */
        margin-top: 10px;
    }}
    .card-underline-{{key}} {{
        width: 40px;
        height: 4px;
        background-color: {color_end};
        border-radius: 2px;
        margin-top: 5px;
    }}
    </style>
    """

    # Apply CSS
    st.markdown(card_css, unsafe_allow_html=True)
    
    # Create the card structure
    card_html = f"""
    <div class="card-{key}">
        <div class="icon-container-{key}">
            {icon}
        </div>
        <div class="card-title-{key}">{title}</div>
        <div class="card-underline-{key}"></div>
    </div>
    """
    
    # Use a button to handle the click and navigation
    col_btn = st.columns(1)[0]
    with col_btn:
        # Streamlit button styled to look invisible over the card
        if st.button(" ", key=key, use_container_width=True):
            # Navigation points to file name in the same directory
            st.switch_page(page_path) 
            
    # Overlay the card HTML using st.markdown
    st.markdown(
        f'<div style="position: relative; top: -250px; z-index: 10;">{card_html}</div>', 
        unsafe_allow_html=True
    )

# --- Main Page Layout ---

st.set_page_config(
    page_title="Corporate Portal",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Removed the st.title and st.markdown for a cleaner look matching the image
# st.title("ZODOPT Corporate Portal")
# st.markdown("### Select an application to begin your work:")

# Center the content better by using columns with padding
col_spacer1, col_main, col_spacer2 = st.columns([1, 4, 1])

with col_main:
    # Create two columns for the card layout
    col1, col2 = st.columns(2)

    # --- Visitplan Card (Left) ---
    with col1:
        # Note: The icon in the image is a generic window/app icon. Using a clipboard for "Visitplan" as a close text approximation.
        nav_card(
            title="Visitplan",
            icon="📋",
            # Updated to point directly to visitors.py
            page_path="visitors.py", 
            color_start=VISITPLAN_COLOR_START,
            color_end=VISITPLAN_COLOR_END,
            key="visitplan_card"
        )

    # --- Conference Booking Card (Right) ---
    with col2:
        # Note: The icon in the image is a calendar/date icon. Using a calendar emoji.
        nav_card(
            title="Conference Booking",
            icon="🗓️",
            # Updated to point directly to conference.py
            page_path="conference.py",
            color_start=CONFERENCE_COLOR_START,
            color_end=CONFERENCE_COLOR_END,
            key="conference_card"
        )
    
# Removed the trailing st.markdown footer for a clean look
