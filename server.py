import os
from fastapi import FastAPI
from agent_lapangan.agent import Payload
from agent_lapangan.agent import main as run_agent_main
from agent_lapangan.agent import _create_session

app = FastAPI(
    title="Agent API",
    description="API untuk mengelola session dan menjalankan agent",
    version="1.0.0",
)

ENV_VARS = {
    "GOOGLE_API_KEY": "",
    "GOOGLE_GENAI_USE_VERTEXAI": "",
}


@app.post("/secret")
async def set_secret(payload: dict):
    if payload:
        for key, value in payload.items():
            if key == "api_key":
                os.environ["GOOGLE_API_KEY"] = value
            elif key == "use_vertex_ai":
                os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1" if value == "1" else "0"


@app.post("/reset-secrets")
async def reset_secrets():
    for key, value in ENV_VARS.items():
        os.environ[key] = value


@app.post("/session")
async def create_session(payload: Payload):
    return await _create_session(payload)


@app.post("/run")
async def run_agent(payload: Payload):
    return await run_agent_main(payload)
