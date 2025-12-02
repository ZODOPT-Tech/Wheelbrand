import streamlit as st

# ---------------------------------------------------------
# Custom CSS (Necessary for consistent styling)
# ---------------------------------------------------------
def load_css():
    """Injects custom CSS for branding and layout aesthetics."""
    # Only including minimal CSS for the login container/button aesthetics
    st.markdown("""
    <style>
    /* General Container adjustments for focus */
    .block-container {
        padding-top: 5rem !important; /* Added padding for standalone page look */
        padding-bottom: 0rem !important;
        max-width: 800px !important;
    }
    
    /* Target Streamlit button structure (Blue Primary) */
    .stButton>button {
        width: 100%;
        min-height: 58px;
        background: #1A5CFF !important;
        color: white !important;
        border: none !important;
        padding: 18px 0 !important;
        border-radius: 12px !important;
        font-size: 20px !important;
        font-weight: 600 !important;
        margin-top: 20px;
        box-shadow: 0 4px 10px rgba(26, 92, 255, 0.4);
        transition: background 0.2s;
    }

    .stButton>button:hover {
        background: #004de6 !important;
    }
    
    /* Hiding back-to-main button label for cleaner presentation */
    #back_to_main_visitor_only button {
        background: none !important;
        box-shadow: none !important;
        color: #6c757d !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        min-height: 30px;
        text-align: left;
    }

    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# PAGE FUNCTION
# ---------------------------------------------------------

def render_visitor_login():
    """Renders the Visitor Login screen."""
    st.title("Visitor Login")
    st.subheader("Manage Your Visit Plan")

    with st.container(border=True):
        st.markdown("Please enter your credentials to manage your visit plan.")
        
        # Input fields
        email = st.text_input("Email Address", key="visitor_email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", key="visitor_password")

        # Hides the Streamlit default labels above the text inputs
        st.markdown('<style>.stTextInput label {display: none;}</style>', unsafe_allow_html=True)

        if st.button("Log In", key="visitor_login_btn", help="Click to log in"):
            # Placeholder for actual login logic
            if email and password:
                st.success(f"Attempting to log in as {email}...")
                # In a real app, this would redirect to the visitor dashboard
            else:
                st.error("Please enter both email and password.")

    # Placeholder back button (will not function fully without the main screen logic)
    if st.button("← Back (Main Screen Not Included)", key="back_to_main_visitor_only"):
        st.info("The Main Screen functionality is not included in this file.")


# ---------------------------------------------------------
# STANDALONE EXECUTION
# ---------------------------------------------------------
if __name__ == "__main__":
    st.set_page_config(layout="centered")
    load_css()
    render_visitor_login()
