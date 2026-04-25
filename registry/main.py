from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import List, Dict
import time
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("registry")

app = FastAPI(title="A2A Agent Registry")

# --- Data Models ---
class AgentRegistration(BaseModel):
    name: str
    description: str
    skills: List[str]
    url: str
    version: str
    ttl: int  # Time-to-live in seconds

class AgentResponse(AgentRegistration):
    last_heartbeat: float

class Envelope(BaseModel):
    task_id: str
    input: str
    context: Dict = {}

class ResponseEnvelope(BaseModel):
    task_id: str
    output: str
    status: str

# --- In-Memory Storage ---
# Key: agent_name, Value: AgentResponse
agents_db: Dict[str, AgentResponse] = {}

# --- Background Task for TTL Expiration ---
async def cleanup_expired_agents():
    """Periodically removes agents that haven't sent a heartbeat."""
    while True:
        current_time = time.time()
        expired_agents = []
        for name, agent in agents_db.items():
            if current_time - agent.last_heartbeat > agent.ttl:
                expired_agents.append(name)
        
        for name in expired_agents:
            logger.info(f"Removing expired agent: {name}")
            del agents_db[name]
        
        await asyncio.sleep(5)  # Check every 5 seconds

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_expired_agents())

# --- Endpoints ---

@app.post("/register", response_model=Dict[str, str])
async def register_agent(agent: AgentRegistration):
    """Registers a new agent or updates an existing one (heartbeat)."""
    agents_db[agent.name] = AgentResponse(
        **agent.dict(),
        last_heartbeat=time.time()
    )
    logger.info(f"Registered/Heartbeat: {agent.name} at {agent.url}")
    return {"status": "registered", "name": agent.name}

@app.get("/agents", response_model=List[AgentResponse])
async def list_agents():
    """Returns a list of all active agents."""
    return list(agents_db.values())

@app.get("/")
async def root():
    return {"message": "A2A Registry Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
