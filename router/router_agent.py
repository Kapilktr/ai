from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import httpx
import asyncio
import logging
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("router")

app = FastAPI(title="A2A Router Agent")

# --- Configuration ---
REGISTRY_URL = "http://localhost:9000"
ROUTER_PORT = 8003

# --- Gemini Configuration ---
api_key = os.getenv("GEMINI_API_KEY")
model = None  # Initialize to None
if not api_key:
    logger.warning("GEMINI_API_KEY not found. Router will use keyword-based fallback routing.")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro")

# --- Data Models ---
class UserRequest(BaseModel):
    query: str
    context: dict = {}

class AgentResponse(BaseModel):
    agent_name: str
    response: str
    status: str

# --- Helper Functions ---
async def get_available_agents():
    """Fetches the list of active agents from the registry."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{REGISTRY_URL}/agents")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch agents: {e}")
            return []

async def select_agent(query: str, agents: list):
    """Uses Gemini to select the best agent for the task."""
    if not agents:
        return None, "No agents available."

    agent_descriptions = "\n".join([f"- {a['name']}: {a['description']} (Skills: {', '.join(a['skills'])})" for a in agents])
    
    prompt = f"""
    You are an intelligent router for a multi-agent system.
    Task: Analyze the user query and select the SINGLE best agent to handle it.
    
    User Query: "{query}"
    
    Available Agents:
    {agent_descriptions}
    
    Output JSON ONLY with the following format:
    {{
        "selected_agent": "agent_name",
        "reasoning": "why you chose this agent",
        "task_input": "extracted input for the agent"
    }}
    
    If no agent is suitable, returning "selected_agent": null.
    """
    
    try:
        if model is None:
             # Fallback: Simple keyword matching if Gemini is not configured
            lower_query = query.lower()
            logger.info(f"Using fallback routing for: {query}")
            if "email" in lower_query or "draft" in lower_query or "write" in lower_query:
                return {"selected_agent": "email_formatter_agent", "task_input": query}, None
            elif "authorized" in lower_query or "allowed" in lower_query or "auth" in lower_query:
                return {"selected_agent": "name_auth_agent", "task_input": query}, None
            elif "meeting" in lower_query or "schedule" in lower_query:
                return {"selected_agent": "meeting_agent", "task_input": query}, None
            elif "hello" in lower_query or "help" in lower_query or "agent" in lower_query or "available" in lower_query:
                agent_list = "\n".join([f"- {a['name']}: {a['description']}" for a in agents])
                return None, f"I am running in Fallback Mode (No Gemini API Key). Available agents:\n{agent_list}\n\nKeywords: 'email', 'authorize', 'meeting'"
            else:
                return None, "No matching agent found. Try keywords: 'email', 'authorize', or 'meeting'."

        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        decision = json.loads(text)
        return decision, None
    except Exception as e:
        logger.error(f"Routing error: {e}")
        return None, str(e)

async def call_agent(agent_url: str, task_input: str, context: dict):
    """Calls the selected agent."""
    payload = {
        "task_id": "router_task", # Simple ID for now
        "input": task_input,
        "context": context
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{agent_url}/process", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Agent call failed: {e}")
            return {"status": "error", "output": f"Agent call failed: {str(e)}"}

# --- Endpoints ---

# @app.post("/chat", response_model=AgentResponse)
# async def chat(request: UserRequest):
#     """Main entry point for user interaction."""
#     logger.info(f"Received query: {request.query}")
    
    # 1. Discovery
    agents = await get_available_agents()
    if not agents:
        return AgentResponse(agent_name="System", response="No agents registered.", status="error")

    # 2. Routing
    decision, error = await select_agent(request.query, agents)
    if error:
        return AgentResponse(agent_name="System", response=f"Routing failed: {error}", status="error")
    
    if not decision or not decision.get("selected_agent"):
        return AgentResponse(agent_name="System", response="No suitable agent found for your request.", status="error")

    # 3. Execution
    target_agent_name = decision["selected_agent"]
    target_agent = next((a for a in agents if a["name"] == target_agent_name), None)
    
    if not target_agent:
        return AgentResponse(agent_name="System", response=f"Selected agent '{target_agent_name}' not found in registry (race condition?).", status="error")

    logger.info(f"Routing to: {target_agent_name}")
    agent_result = await call_agent(target_agent["url"], decision["task_input"], request.context)
    
    # 4. Response
    return AgentResponse(
        agent_name=target_agent_name,
        response=agent_result.get("output", "No output"),
        status=agent_result.get("status", "unknown")
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=ROUTER_PORT)
