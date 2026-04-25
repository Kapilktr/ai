from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import asyncio
import logging
import os
import sys
import datetime

# Ensure shared utils can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from agents.utils import register_with_registry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("meeting_agent")

app = FastAPI(title="Meeting Scheduler Agent")

# --- Configuration ---
REGISTRY_URL = "http://localhost:9000"
AGENT_PORT = 8004
AGENT_HOST = "localhost"

AGENT_METADATA = {
    "name": "meeting_agent",
    "description": "Manages meeting schedules and lists upcoming meetings.",
    "skills": ["scheduling", "calendar", "meetings"],
    "url": f"http://{AGENT_HOST}:{AGENT_PORT}",
    "version": "1.0.0",
    "ttl": 30
}

# --- Mock Database ---
meetings = [
    {"id": 1, "title": "Daily Standup", "time": "10:00 AM"},
    {"id": 2, "title": "Project Review", "time": "2:00 PM"},
]

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
    """Handles meeting related queries."""
    query = envelope.input.lower()
    logger.info(f"Processing meeting request: {query}")

    if "list" in query or "show" in query:
        meeting_list = "\n".join([f"- {m['title']} at {m['time']}" for m in meetings])
        output = f"Here are your upcoming meetings:\n{meeting_list}"
    elif "schedule" in query or "book" in query:
        # Mock scheduling logic
        output = f"Mock: scheduled a meeting based on '{envelope.input}'. (This is a simplified demo)"
    else:
        output = "I can help you list or schedule meetings. What would you like to do?"

    return ResponseEnvelope(
        task_id=envelope.task_id,
        output=output,
        status="success"
    )

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(register_with_registry(REGISTRY_URL, AGENT_METADATA, AGENT_METADATA["ttl"]))
    logger.info(f"Agent started on port {AGENT_PORT}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
