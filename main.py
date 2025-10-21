import streamlit as st

st.set_page_config(page_title="CV Reviewer", page_icon="📜")


def main():
    st.title("Welcome to the CV Reviewer App")
    st.markdown(
        """
        This application helps you review and analyze CVs efficiently.
        
        **Features:**
        - Upload your CV in various formats (PDF).
        - Get insights and suggestions for improvement.
        
        """
    )


pg = st.navigation(
    [
        st.Page(main, title="Home", icon="🏠"),
        st.Page("pages/conversation_page.py", title="Conversation", icon="💬"),
        st.Page("pages/setting_page.py", title="Settings", icon="⚙️"),
    ],
    position="top",
)
pg.run()
