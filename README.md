# 🌍 AI Travel Planner Agent

An intelligent AI agent that helps users plan personalized 2-day trips using real-time data, memory, and multi-tool reasoning.

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

## Evaluation Metrics

The agent is evaluated on:
- **Agent Logic**: Smart tool selection and planning
- **LLM + RAG**: Effective retrieval from Tavily search
- **Memory**: Session continuity and preference recall
- **Code Quality**: Modular, documented codebase
- **Deployment**: Live cloud API on Railway
