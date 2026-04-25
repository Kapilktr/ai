# Agent-to-Agent (A2A) System

A decentralized, registry-driven agent system using FastAPI and Google Gemini.

## 📂 Structure

- `registry/`: Central discovery service (Port 9000)
- `agents/`: Independent agent services
    - `email_agent/`: Formats emails using Gemini (Port 8001)
    - `name_agent/`: Validates names (Port 8002)
    - `meeting_agent/`: Mock meeting scheduler (Port 8004)
- `router/`: Main user interface (Port 8003)

## 🚀 Setup

1.  **Environment**:
    ```bash
    cd a2a-system
    # Create .env file with your Gemini API Key
    echo GEMINI_API_KEY=your_key_here > .env
    ```

2.  **Install Dependencies**:
    ```bash
    pip install fastapi uvicorn httpx google-generativeai python-dotenv
    ```

## 🏃 Running the System

### Option 1: Automated (Recommended)
You can start all services at once using the provided PowerShell script:

```powershell
.\run_system.ps1
```

This will open 5 new terminal windows, one for each component.

### Option 2: Manual (Step-by-Step)
If you prefer to run them manually, open 5 separate terminal windows in `d:\GenAI\a2a` and run:

**Terminal 1: Registry**
```bash
python a2a-system/registry/main.py
```

**Terminal 2: Name Agent**
```bash
python a2a-system/agents/name_agent/app.py
```

**Terminal 3: Email Agent**
```bash
python a2a-system/agents/email_agent/app.py
```

**Terminal 4: Meeting Agent**
```bash
python a2a-system/agents/meeting_agent/app.py
```

**Terminal 5: Router**
```bash
python a2a-system/router/router_agent.py
```

## 💻 Client Interaction

Instead of using `curl`, you can use the interactive CLI client:

1.  Open a new terminal window.
2.  Activate the environment: `.venv\Scripts\activate` or just use `python` from the root if venv is active.
3.  Run the client:
    ```bash
    python client.py
    ```
4.  Type your queries and see the agent responses!

## 🧪 Usage Examples

**Subject: Email Formatting**
> "Draft a short email to the team about the server outage."
> *Router should select `email_formatter_agent`.*

**Example 3: List Meetings**
```bash
curl -X POST "http://localhost:8003/chat" \
     -H "Content-Type: application/json" \
     -d '{"query": "What meetings do I have today?"}'
```

## 🧠 How it Works

1.  **Registration**: Agents start up and register with the **Registry** (Port 9000). They send heartbeats every few seconds.
2.  **Discovery**: The **Router** (Port 8003) queries the Registry to see who is online.
3.  **Routing**: The Router uses **Gemini** to decide which agent matches the user's intent.
4.  **Execution**: The Router calls the selected agent (A2A communication).
5.  **Response**: The result is returned to the user.
