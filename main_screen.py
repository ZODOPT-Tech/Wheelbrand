import streamlit as st

def render_main_screen():

    # ---------------- HEADER ----------------
    st.markdown(
        """
        <style>
        .header-box {
            background: linear-gradient(90deg, #2356F6, #5A38F9, #8A23FF);
            padding: 40px;
            border-radius: 25px;
            margin-bottom: 40px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.container():
        st.markdown('<div class="header-box">', unsafe_allow_html=True)

        colA, colB = st.columns([2, 1])
        with colA:
            st.markdown(
                "<h1 style='color:white; font-size:40px; font-weight:800;'>ZODOPT MEETEASE</h1>",
                unsafe_allow_html=True
            )
        with colB:
            st.image("zodopt.png", width=150)

        st.markdown("</div>", unsafe_allow_html=True)

    # --------------- MAIN BODY CARDS ----------------
    col1, col2 = st.columns(2, gap="large")

    with col1:
        with st.container(border=True):
            st.write("")
            st.write("### 📅")
            st.write("")
            if st.button("Visit Plan", key="visit_btn"):
                st.session_state.current_page = "visitor_login"
                st.rerun()

    with col2:
        with st.container(border=True):
            st.write("")
            st.write("### 📚")
            st.write("")
            if st.button("Conference Booking", key="conference_btn"):
                st.session_state.current_page = "conference_login"
                st.rerun()

    st.caption("A ZODOPT Visitor and Conference Management System.")


# Call the page renderer
render_main_screen()
