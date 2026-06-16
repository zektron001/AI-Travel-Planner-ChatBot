# 🌍 AI Travel Planner Agent

An intelligent AI agent that helps users plan personalized 2-day trips using real-time data, memory, and multi-tool reasoning. To check on the project please follow this [link](https://ai-travel-planner-production-3ea3.up.railway.app/).

## Architecture

```
User → FastAPI → LangChain Agent → Tools (Weather, Hotels, Flights, Search)
                      ↕
              Short-term Memory (Conversation)
                      ↕
              Long-term Memory (FAISS Vector DB)
```

## Features

- 🤖 **GPT-4o powered** agent with tool-use and reasoning
- 🔍 **Web Search** via Tavily for real attraction/restaurant data
- 🌤️ **Live Weather** via OpenWeatherMap
- 🏨 **Hotel Search** with budget filtering
- ✈️ **Flight Search** with price filtering
- 🧠 **Short-term memory** — maintains conversation context per session
- 💾 **Long-term memory** — FAISS vector DB remembers user preferences across sessions
- 📋 **Multi-hop planning** — breaks your trip into morning/afternoon/evening slots

## Setup

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd travel-agent
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required API keys:
| Key | Where to get |
|-----|-------------|
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) — free tier |
| `OPENWEATHER_API_KEY` | [openweathermap.org/api](https://openweathermap.org/api) — free |

### 3. Run Locally

```bash
uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive API docs.

## API Reference

### POST `/chat`
Send a message to the travel agent.

**Request:**
```json
{
  "message": "Plan a 2-day trip to Tokyo for a solo traveler on a $100/day budget",
  "session_id": "my-session-123"
}
```

**Response:**
```json
{
  "reply": "Here's your personalized Tokyo itinerary...",
  "session_id": "my-session-123"
}
```

### GET `/session/{session_id}/history`
Retrieve full conversation history.

### DELETE `/session/{session_id}`
Clear a session (start fresh).

### GET `/health`
Health check.

## Example Conversations

```
User: Plan a 2-day trip to Paris for a couple on a mid-range budget
Agent: [searches attractions, weather, hotels, flights → builds full itinerary]

User: We have a dog, can we find pet-friendly options?
Agent: [remembers preference, searches pet-friendly hotels]

User: What's the weather like?
Agent: [uses get_weather tool → gives current Paris weather]
```

## Deployment on Railway

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
3. Railway auto-detects `railway.json`
4. Add environment variables in Railway dashboard (no quotes around values):
   - `OPENAI_API_KEY`
   - `TAVILY_API_KEY`
   - `OPENWEATHER_API_KEY`
5. Deploy! 🚀

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | OpenAI GPT-4o |
| Agent Framework | LangChain |
| Short-term Memory | In-memory conversation history |
| Long-term Memory | FAISS vector database |
| Web Search | Tavily API |
| Weather | OpenWeatherMap API |
| API Framework | FastAPI |
| Deployment | Railway |

## Technical Design

### Architecture

The system follows a single-service architecture where FastAPI serves both the REST API and the static frontend. All requests flow through one entry point (`main.py`), which delegates to the LangChain agent. This avoids the complexity of a separate frontend deployment while keeping the backend modular.

```
HTTP Request
    ↓
FastAPI (main.py)
    ↓
chat() — planner.py
    ├── MemoryManager.search_knowledge_base()   # PDF RAG context
    ├── MemoryManager.get_relevant_preferences() # User preference recall
    ├── build_agent() → AgentExecutor
    │       ├── ChatOpenAI (GPT-4o)
    │       └── Tools: [multi_hop_search, search_attractions,
    │                    get_weather, search_hotels, search_flights]
    └── MemoryManager.add_message()             # Store turn in session
```

Each request rebuilds the agent fresh (`build_agent()` is called per request) to avoid shared state across sessions.

---

### Tool Selection

| Tool | API | Rationale |
|------|-----|-----------|
| `multi_hop_search` | Tavily | Performs 3 chained searches (overview → districts → experiences) to build richer context than a single query. Used first for any new destination. |
| `search_attractions` | Tavily | Used for targeted follow-up queries (specific restaurants, activities) after the initial multi-hop pass. |
| `get_weather` | OpenWeatherMap | Free tier supports real-time weather by city name — sufficient for the agent's needs without geocoding complexity. |
| `search_hotels` | Mock data | Simulates hotel results with budget filtering. Avoids paid booking APIs while demonstrating tool-use and filtering logic. |
| `search_flights` | Mock data | Same rationale as hotels — demonstrates multi-tool orchestration without requiring a live flight API. |

**Why Tavily over direct Google/Bing search?** Tavily is purpose-built for LLM agents — it returns structured `answer` + `results` fields and handles deduplication, making it easier to parse than raw HTML scraping.

**Why GPT-4o?** The OpenAI Functions API used by LangChain's `create_openai_functions_agent` requires a model that supports function calling natively. GPT-4o offers the best balance of reasoning quality and speed for multi-step tool orchestration.

---

### Memory Design

The system implements a two-tier memory architecture:

**Short-term memory (per-session conversation history)**
- Stored in a Python dict keyed by `session_id`
- Capped at the last 20 messages to prevent context overflow
- Passed directly into the LangChain agent as `chat_history` on every request
- Cleared on `DELETE /session/{session_id}`

**Long-term memory (FAISS vector store)**
- A single FAISS index is shared across all sessions (singleton `MemoryManager`)
- Serves two purposes:
  1. **Knowledge base** — PDFs in `Data/` are chunked into 500-character segments and embedded at startup, giving the agent offline knowledge about specific destinations
  2. **Preference store** — when a user expresses preferences (budget, dietary, accessibility), the message is embedded and added to the same index for future recall
- At query time, `similarity_search` retrieves the top-k relevant chunks and injects them into the system prompt as context

**Trade-off:** FAISS is in-memory only — all stored preferences and session history are lost on app restart. For a production system this would be replaced with a persistent vector DB (e.g. Pinecone) and a session store (e.g. Redis).

---

## Evaluation Metrics

The agent is evaluated on:
- **Agent Logic**: Smart tool selection and planning
- **LLM + RAG**: Effective retrieval from Tavily search
- **Memory**: Session continuity and preference recall
- **Code Quality**: Modular, documented codebase
- **Deployment**: Live cloud API on Railway
