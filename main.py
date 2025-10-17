import streamlit as st
import requests
import base64
import mimetypes
import time
import math
import uuid

SERVER = "http://localhost:8000"
APP_NAME = "agent_lapangan"
USER_ID = "web_user"

st.title("CV Reviewer (Streamlit + ADK)")

def _safe_partial_markdown(md: str) -> str:
    """
    Jika code fence ``` belum genap, tambahkan penutup sementara
    supaya render nggak pecah saat streaming.
    """
    fence_count = md.count("```")
    if fence_count % 2 == 1:
        return md + "\n```"
    return md


def stream_markdown(
    text: str, placeholder, cps: int = 80, min_chunk: int = 8, max_chunk: int = 60
):
    """
    Stream teks markdown ke placeholder dengan efek ngetik.
    - cps: chars per second (kira-kira kecepatan ngetik)
    - min/max_chunk: ukuran potongan per update biar smooth
    """
    if not text:
        return

    # adaptif: chunk size berdasarkan panjang teks
    # makin panjang, makin gede chunk biar nggak kelamaan
    L = len(text)
    target_updates = max(20, min(150, L // 10))
    chunk = max(min_chunk, min(max_chunk, math.ceil(L / target_updates)))

    buf = ""
    for i in range(0, L, chunk):
        buf = text[: i + chunk]
        placeholder.markdown(_safe_partial_markdown(buf))
        # jeda sesuai cps (kasar)
        sleep_s = max(0.005, chunk / max(1, cps))
        time.sleep(sleep_s)


def render_assistant_parts_streaming(parts):
    """
    Render assistant parts dengan efek ngetik untuk part 'text'.
    Attachment (inlineData) ditampilkan instan.
    """
    if not parts:
        st.markdown("_No response parts returned._")
        return

    for part in parts:
        if "text" in part and part["text"]:
            ph = st.empty()
            stream_markdown(part["text"], ph, cps=90)
        elif "inlineData" in part:
            meta = part["inlineData"]
            name = meta.get("displayName", "attachment")
            mime = meta.get("mimeType", "application/octet-stream")
            st.caption(f"📎 **{name}**")

def ensure_session():
    if "session_id" not in st.session_state:
        st.session_state.session_id = (
            f"session_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        )
        # Create a new session on the ADK server
        requests.post(
            f"{SERVER}/apps/{APP_NAME}/users/{USER_ID}/sessions/{st.session_state.session_id}",
            json={},
            timeout=30,
        )
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
            "mimeType": mime,
        }
    }


def send_to_agent(parts):
    """Send message parts to ADK and return assistant parts."""
    payload = {
        "app_name": APP_NAME,
        "user_id": USER_ID,
        "session_id": st.session_state.session_id,
        "new_message": {
            "role": "user",
            "parts": parts,
        },
    }
    resp = requests.post(f"{SERVER}/run", json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    # Expected: list of messages; take first assistant message
    # Safeguards for different shapes just in case
    assistant_parts = []
    try:
        # Common shape: [{"content":{"parts":[...]}}]
        first = data[0]
        content = first.get("content") if isinstance(first, dict) else None
        assistant_parts = (content or {}).get("parts", [])
    except Exception:
        assistant_parts = []

    # Fallback: if server returns a flat text
    if not assistant_parts and isinstance(data, dict) and "text" in data:
        assistant_parts = [{"text": data["text"]}]

    if (
        not assistant_parts
        and isinstance(data, list)
        and data
        and isinstance(data[0], str)
    ):
        assistant_parts = [{"text": "\n".join(data)}]

    return assistant_parts


def render_part(part):
    """Render a single part inside a chat message bubble."""
    if "text" in part and part["text"]:
        st.markdown(part["text"])
    elif "inlineData" in part:
        meta = part["inlineData"]
        name = meta.get("displayName", "attachment")
        mime = meta.get("mimeType", "application/octet-stream")
        size_info = ""
        # we can't reconstruct original bytes here (we only keep b64 inside state if needed)
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
            # Important: we need to re-seek afterwards if you also want to re-read later
            user_parts.append(file_part_from_uploaded(_f))

    # Push user message into history
    st.session_state.messages.append({"role": "user", "parts": user_parts})

    # Show the user bubble immediately
    with st.chat_message("user"):
        for p in user_parts:
            render_part(p)

    # Call agent and render assistant reply
    with st.chat_message("assistant"):
        with st.spinner("Generating response..."):
            assistant_parts = send_to_agent(user_parts)
            if not assistant_parts:
                assistant_parts = [{"text": "_(No response parts returned.)_"}]

            # STREAMING EFFECT here
            render_assistant_parts_streaming(assistant_parts)

    # Save assistant reply to history
    st.session_state.messages.append({"role": "assistant", "parts": assistant_parts})
