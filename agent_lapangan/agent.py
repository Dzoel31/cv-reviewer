from typing import Union, Optional, List
from pydantic import BaseModel
from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from .prompt import REVIEW_PROMPT
import base64


class InlineData(BaseModel):
    displayName: Optional[str] = None
    data: Union[bytes, str]
    mimetype: str


class MessagePart(BaseModel):
    text: Optional[str] = None
    inlineData: Optional[InlineData] = None


class Message(BaseModel):
    role: str
    parts: List[MessagePart]


class Payload(BaseModel):
    app_name: str
    user_id: str
    session_id: str
    new_message: Optional[Message] = None


root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="Review",
    instruction=REVIEW_PROMPT,
)

session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name="agent_lapangan",
    session_service=session_service,
)


def _part_from_msg(msg: MessagePart) -> types.Part:
    if msg.inlineData is not None:
        raw = msg.inlineData.data
        # Decode base64 strings if possible; otherwise, encode string to bytes
        if isinstance(raw, str):
            try:
                raw_bytes = base64.b64decode(raw, validate=True)
            except Exception:
                raw_bytes = raw.encode()
        elif isinstance(raw, bytes):
            raw_bytes = raw
        else:
            raw_bytes = str(raw).encode()

        mime = msg.inlineData.mimetype or None
        return types.Part(inline_data=types.Blob(mime_type=mime, data=raw_bytes))

    return types.Part(text=(msg.text or ""))


async def _create_session(payload: Payload):
    session = await session_service.create_session(
        app_name=payload.app_name,
        user_id=payload.user_id,
        session_id=payload.session_id,
    )

    return session.model_dump()


async def main(payload: Union[Payload, dict]):
    # Allow callers to pass either a dict or the Payload model
    if not isinstance(payload, Payload):
        payload = Payload.model_validate(payload)  # Pydantic v2
        # For Pydantic v1, replace with: payload = Payload.parse_obj(payload)
    
    if payload.new_message is None:
        return []
    
    content = types.Content(
        role=payload.new_message.role,
        parts=[_part_from_msg(m) for m in payload.new_message.parts],
    )

    async for event in runner.run_async(
        user_id=payload.user_id,
        session_id=payload.session_id,
        new_message=content,
    ):
        if event.is_final_response() and event.content:
            if event.content.parts:
                return [p.dict() for p in event.content.parts]

    return []
