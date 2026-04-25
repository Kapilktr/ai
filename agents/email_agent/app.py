from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Ensure shared utils can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from agents.utils import register_with_registry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("email_agent")

app = FastAPI(title="Email Formatter Agent")

# --- Configuration ---
REGISTRY_URL = "http://localhost:9000"
AGENT_PORT = 8001
AGENT_HOST = "localhost"

AGENT_METADATA = {
    "name": "email_formatter_agent",
    "description": "Formats professional emails based on user input and context.",
    "skills": ["email_drafting", "communication", "formatting"],
    "url": f"http://{AGENT_HOST}:{AGENT_PORT}",
    "version": "1.0.0",
    "ttl": 30
}

# --- Gemini Configuration ---
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.warning("GEMINI_API_KEY not found in environment variables. Agent may fail.")
else:
    genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-pro")

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
    """Generates a professional email using Gemini."""
    logger.info(f"Processing email request: {envelope.input}")
    
    try:
        prompt = f"""
        You are an expert email composer.
        Task: Draft a professional email based on the following input.
        Input: {envelope.input}
        Context: {envelope.context}
        
        Only return the body of the email. Do not include subject lines unless asked.
        """
        
        response = model.generate_content(prompt)
        email_content = response.text
        
        return ResponseEnvelope(
            task_id=envelope.task_id,
            output=email_content,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error generating email: {e}")
        return ResponseEnvelope(
            task_id=envelope.task_id,
            output=f"Error generating email: {str(e)}",
            status="error"
        )

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(register_with_registry(REGISTRY_URL, AGENT_METADATA, AGENT_METADATA["ttl"]))
    logger.info(f"Agent started on port {AGENT_PORT}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
