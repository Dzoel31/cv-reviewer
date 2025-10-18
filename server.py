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

@app.post("/secret")
async def set_secret(payload: dict):
    if payload:
        os.environ["GOOGLE_API_KEY"] = payload.get('api_key', '')
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = payload.get('use_vertex_ai', 'false').lower()

@app.post("/session")
async def create_session(payload: Payload):
    return await _create_session(payload)

@app.post("/run")
async def run_agent(payload: Payload):
    return await run_agent_main(payload)

