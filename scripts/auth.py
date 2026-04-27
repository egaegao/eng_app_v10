import streamlit as st

def login_screen():
    st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        margin-top: 40px;
        margin-bottom: 20px;
        color: #0f172a;
    }

    .quote-text {
        text-align: center;
        max-width: 600px;
        margin: 0 auto 10px auto;
        color: #334155;
        font-size: 1rem;
        font-style: italic;
    }

    .author-text {
        text-align: center;
        font-size: 0.75rem;
        margin-bottom: 40px;
        color: #64748b;
        font-weight: 700;
        letter-spacing: 0.15em;
    }

    div.stButton > button {
        background-color: #2563eb !important;
        color: white !important;
        height: 42px !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if not st.session_state['authenticated']:
        st.markdown("<style>section[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

        st.markdown('<h1 class="main-title">OPSAPP</h1>', unsafe_allow_html=True)

        st.markdown("""
        <div class="quote-text">
        "Disiplin kecil setiap hari akan menghasilkan hasil besar di masa depan."
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="author-text">Mining Operation System</div>', unsafe_allow_html=True)

        _, col, _ = st.columns([1.5,1,1.5])

        with col:
            password = st.text_input(
                "Access Code",
                type="password",
                placeholder="••••••",
                label_visibility="collapsed"
            )

            if st.button("Login"):
                if password == "pms":
                    st.session_state['authenticated'] = True
                    st.rerun()
                else:
                    st.error("Access ditolak")

        st.stop()