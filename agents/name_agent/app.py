from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import asyncio
import logging
import os
import sys

# Ensure shared utils can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from agents.utils import register_with_registry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("name_agent")

app = FastAPI(title="Name Authorization Agent")

# --- Configuration ---
REGISTRY_URL = "http://localhost:9000"
AGENT_PORT = 8002
AGENT_HOST = "localhost" # or 0.0.0.0, but using localhost for simplicity

AGENT_METADATA = {
    "name": "name_auth_agent",
    "description": "Checks if a name is authorized to access the system.",
    "skills": ["name_validation", "authorization"],
    "url": f"http://{AGENT_HOST}:{AGENT_PORT}",
    "version": "1.0.0",
    "ttl": 30
}

# --- Authorized Names ---
AUTHORIZED_NAMES = ["Alice", "Bob", "Charlie", "David"] # Hardcoded list

# --- Data Models ---
class RequestEnvelope(BaseModel):
    task_id: str
    input: str
    context: dict = {}

class ResponseEnvelope(BaseModel):
    task_id: str
    output: str
    status: str

# --- Endpoints ---

@app.post("/process", response_model=ResponseEnvelope)
async def process_request(envelope: RequestEnvelope):
    """Checks if the input name is in the authorized list."""
    name_to_check = envelope.input.strip()
    logger.info(f"Processing request for name: {name_to_check}")

    is_authorized = name_to_check in AUTHORIZED_NAMES

    if is_authorized:
        output_message = f"Authorized: '{name_to_check}' is in the system."
        status = "success"
    else:
        output_message = f"Denied: '{name_to_check}' is NOT authorized."
        status = "success" # The check itself succeeded, even if denied

    return ResponseEnvelope(
        task_id=envelope.task_id,
        output=output_message,
        status=status
    )

@app.on_event("startup")
async def startup_event():
    # Start the background registration task
    asyncio.create_task(register_with_registry(REGISTRY_URL, AGENT_METADATA, AGENT_METADATA["ttl"]))
    logger.info(f"Agent started on port {AGENT_PORT}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
