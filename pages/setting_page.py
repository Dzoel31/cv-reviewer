import streamlit as st
import os
import requests

st.set_page_config(page_title="Setting Page", page_icon=":gear:", layout="wide")

SERVER = os.getenv("ADK_SERVER", "http://localhost:8000")
APP_NAME = os.getenv("APP_NAME", "agent_lapangan")

DEFAULTS = {
    "GEMINI_API_KEY": "",
    "USE_VERTEX_AI": False,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

st.title("Settings")
st.markdown("Configure the application settings below.")

st.session_state.GEMINI_API_KEY = st.text_input(
    "Google API Key", type="password", value=st.session_state.GEMINI_API_KEY
)

st.session_state.USE_VERTEX_AI = st.checkbox(
    "Use Vertex AI", value=st.session_state.USE_VERTEX_AI
)


def _apply_settings():
    try:
        requests.post(
            f"{SERVER}/secret",
            json={
                "api_key": st.session_state.GEMINI_API_KEY,
                "use_vertex_ai": str(1 if st.session_state.USE_VERTEX_AI else 0),
            },
            timeout=30,
        )
    except Exception as e:
        st.error(f"Error applying settings: {e}")


save = st.button("Save Settings", on_click=_apply_settings)
if save:
    st.success("Settings saved successfully.")
