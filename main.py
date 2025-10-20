import streamlit as st
import requests
import base64
import mimetypes
import time
import uuid
import os

SERVER = os.getenv("ADK_SERVER", "http://localhost:8000")
APP_NAME = os.getenv("APP_NAME", "agent_lapangan")

st.title("CV Reviewer (Streamlit + ADK)")

st.sidebar.header("Configuration")
st.sidebar.markdown("""
Configure the application settings below.""")
# Credentials
api_key = st.sidebar.text_input("Google API Key", type="password")
use_vertex_ai = st.sidebar.checkbox("Use Vertex AI", value=False)


def reset_environment():
    """Reset environment variables on the server."""
    try:
        requests.post(f"{SERVER}/reset-secrets", timeout=30)
    except Exception as e:
        st.error(f"Error resetting environment: {e}")


def init_session():
    if "initialized" not in st.session_state:
        reset_environment()
        st.session_state.initialized = True


init_session()


def _save_settings() -> None:
    try:
        requests.post(
            f"{SERVER}/secret",
            json={
                "api_key": api_key,
                "use_vertex_ai": str(1 if use_vertex_ai else 0),
            },
            timeout=30,
        )
    except Exception as e:
        st.error(f"Error saving settings: {e}")


st.sidebar.button("Save Settings", on_click=_save_settings)


def _create_server_session():
    """Create a new session on the ADK server for the current local session_id/user_id."""
    payload = {
        "app_name": APP_NAME,
        "user_id": st.session_state.user_id,
        "session_id": st.session_state.session_id,
    }
    response = requests.post(
        f"{SERVER}/session",
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    print("Created (or recreated) session on server:", data)


def ensure_session():
    if "session_id" not in st.session_state:
        try:
            st.session_state.session_id = (
                f"session_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            )
            st.session_state.user_id = f"user_{uuid.uuid4().hex[:8]}"
            _create_server_session()
        except Exception as e:
            st.error(f"Error creating session on server: {e}")
            st.stop()
    if "messages" not in st.session_state:
        # Each item: {"role": "user"|"assistant", "parts": [{"text":...} or {"inlineData":{...}}]}
        st.session_state.messages = []


ensure_session()


def file_part_from_uploaded(_file):
    """Convert a Streamlit UploadedFile to ADK inlineData part."""
    file_bytes = _file.read()
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    mime = (
        _file.type or mimetypes.guess_type(_file.name)[0] or "application/octet-stream"
    )
    return {
        "inlineData": {
            "displayName": _file.name,
            "data": b64,
            # Server expects 'mimetype' (per Pydantic model InlineData)
            "mimetype": mime,
        }
    }


def send_to_agent(parts):
    """Send message parts to ADK and return assistant parts."""
    payload = {
        "app_name": APP_NAME,
        "user_id": st.session_state.user_id,
        "session_id": st.session_state.session_id,
        "new_message": {
            "role": "user",
            "parts": parts,
        },
    }

    try:
        resp = requests.post(f"{SERVER}/run", json=payload, timeout=120)
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            # Auto-recover if backend session was lost (e.g., server restart)
            body = ""
            try:
                body = resp.text or ""
            except Exception:
                body = ""
            if "session not found" in body.lower():
                # Recreate session on server and retry once
                _create_server_session()
                resp = requests.post(f"{SERVER}/run", json=payload, timeout=120)
                resp.raise_for_status()
            else:
                raise
        data = resp.json()

        # Parse according to documented schema: a list of part-like dicts
        # Example item: {"text": "..."} or {"inline_data": {"mime_type": "...", "data": "..."}}
        assistant_parts = []
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    # handle list of strings fallback
                    if isinstance(item, str):
                        assistant_parts.append({"text": item})
                    continue
                if item.get("text"):
                    assistant_parts.append({"text": item.get("text")})
                elif item.get("inline_data"):
                    inline = item.get("inline_data") or {}
                    # Map server's inline_data to UI's inlineData
                    mime = None
                    name = "attachment"
                    if isinstance(inline, dict):
                        mime = inline.get("mime_type") or inline.get("mimetype")
                        name = (
                            inline.get("display_name")
                            or inline.get("displayName")
                            or name
                        )
                    assistant_parts.append(
                        {
                            "inlineData": {
                                "displayName": name,
                                # Keep UI compatible key; render supports mimeType|mimetype
                                "mimeType": mime or "application/octet-stream",
                            }
                        }
                    )
        elif isinstance(data, dict) and "text" in data:
            # Fallback: single dict with text
            assistant_parts = [{"text": data["text"]}]
        # Final fallback: if we collected strings earlier but none now
        if (
            not assistant_parts
            and isinstance(data, list)
            and data
            and isinstance(data[0], str)
        ):
            assistant_parts = [{"text": "\n".join(data)}]

        return assistant_parts
    except Exception as _:
        return [{"text": "_(Error occurred while contacting agent.)_"}]


def render_part(part):
    """Render a single part inside a chat message bubble."""
    if "text" in part and part["text"]:
        st.markdown(part["text"])
    elif "inlineData" in part:
        meta = part["inlineData"]
        name = meta.get("displayName", "attachment")
        mime = (
            meta.get("mimeType") or meta.get("mimetype") or "application/octet-stream"
        )
        st.caption(f"📎 **{name}** ({mime})")


for msg in st.session_state.messages:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        for p in msg.get("parts", []):
            render_part(p)


user_input = st.chat_input(
    "Enter your message here...",
    key="input_user",
    accept_file=True,
    file_type=["pdf"],
)

if user_input is not None:
    # Build user parts
    user_parts = []
    if getattr(user_input, "text", None):
        user_parts.append({"text": user_input.text})

    files = getattr(user_input, "files", None)
    if files:
        # support multiple files gracefully
        for _f in files:
            if _f is None:
                continue
            user_parts.append(file_part_from_uploaded(_f))

    # Push user message into history
    st.session_state.messages.append({"role": "user", "parts": user_parts})

    # Show the user bubble immediately
    with st.chat_message("user"):
        for p in user_parts:
            render_part(p)

    # Call agent and render assistant reply (no streaming)
    with st.chat_message("assistant"):
        with st.spinner("Generating response..."):
            assistant_parts = send_to_agent(user_parts)
            if not assistant_parts:
                assistant_parts = [{"text": "_(No response parts returned.)_"}]
            for p in assistant_parts:
                render_part(p)

    # Save assistant reply to history
    st.session_state.messages.append({"role": "assistant", "parts": assistant_parts})
