import streamlit as st
import importlib

# Set the page configuration to wide layout to use the full screen width
st.set_page_config(layout="wide")

# -------------------- Initialize State --------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

def navigate_to(page):
    st.session_state.current_page = page
    st.rerun()

# -------------------- Page Loader --------------------
def load_page():

    routes = {
        "home": {"module": None, "fn": None},
        "visit": {"module": "visitor", "fn": "visitor_main"},
        "conference": {"module": "conference_page", "fn": "conference_main"},
    }

    page = st.session_state.current_page

    if page == "home":
        return render_home()

    route_info = routes.get(page)
    if not route_info:
        st.error("Invalid Page Requested")
        return

    module = importlib.import_module(route_info["module"])
    fn = getattr(module, route_info["fn"])
    fn(navigate_to)


# ==================================================================
#                            HOME PAGE
# ==================================================================
def render_home():

    # Load Logo
    from PIL import Image
    from io import BytesIO
    import base64
    logo = Image.open("zodopt.png")
    buf = BytesIO()
    logo.save(buf, format="PNG")
    logo_b64 = base64.b64encode(buf.getvalue()).decode()

    st.markdown("""
    <style>
    .header {
        width: 100%;
        padding: 25px 40px;
        border-radius: 25px;
        background: linear-gradient(90deg,#1e62ff,#8a2eff);
        color: white;
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 40px;
    }
    .header-title { font-size: 34px; font-weight: 700; }

    .card {
        background: white;
        padding: 60px;
        border-radius: 25px;
        box-shadow: 0px 8px 20px rgba(0,0,0,0.08);
        text-align: center;
        width: 100%;
        transition: 0.2s;
    }
    .card:hover { transform: translateY(-5px); }

    .icon-circle {
        width: 140px; height: 140px; border-radius: 50%;
        display: flex; justify-content: center; align-items: center;
        font-size: 60px; color: white; margin: auto;
    }
    .violet { background: linear-gradient(135deg,#4d7cff,#b312ff); }
    .green { background: #00a884; }

    .card-text-btn {
        font-size: 28px;
        font-weight: 700;
        color: #222;
        margin-top: 25px;
        cursor: pointer;
    }
    .card-text-btn:hover {
        text-decoration: underline;
    }

    </style>
    """, unsafe_allow_html=True)

    # ---------- HEADER ----------
    st.markdown(
        f"""
        <div class="header">
            <div class="header-title">ZODOPT MEETEASE</div>
            <img src="data:image/png;base64,{logo_b64}" style="height:70px;">
        </div>
        """, unsafe_allow_html=True
    )

    # ---------- CARDS ----------
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
            <div class="card">
                <div class="icon-circle violet">📅</div>
        """, unsafe_allow_html=True)

        # ---- CLICKABLE TEXT ----
        if st.button("Visit Plan", use_container_width=True):
            navigate_to("visit")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="card">
                <div class="icon-circle green">📘</div>
        """, unsafe_allow_html=True)

        if st.button("Conference Booking", use_container_width=True):
            navigate_to("conference")

        st.markdown("</div>", unsafe_allow_html=True)


# -------------------- RUN APP --------------------
load_page()
