import streamlit as st


intro_page = st.Page("pages/Intro.py", title="Info input", icon="👋")
chat_page = st.Page("pages/Chatbot_generator.py", title="Chatbot generator", icon="💬")
deterministic_page = st.Page("pages/Deterministic_generator.py", title="Deterministic generator", icon="⚙️")
readme = st.Page("pages/README.py", title="Readme", icon="📄")

pg = st.navigation(
        {
            "Start here": [intro_page],
            "Choose how to generate input": [chat_page, deterministic_page],
            "About the app": [readme]
        }
    )
pg.run()