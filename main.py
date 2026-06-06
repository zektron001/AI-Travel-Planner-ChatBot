from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import uuid
import os

load_dotenv()

from app.agent.planner import chat
from app.memory.manager import memory_manager

app = FastAPI(
    title="AI Travel Planner",
    description="An intelligent AI agent that plans personalized 2-day trips using real-time data.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


class SessionClearResponse(BaseModel):
    message: str
    session_id: str


@app.get("/", include_in_schema=False)
def root():
    return FileResponse("static/index.html")


@app.get("/health", tags=["Health"])
def health():
    return {"status": "AI Travel Planner is running", "version": "1.0.0"}


@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
def chat_endpoint(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    session_id = request.session_id or str(uuid.uuid4())
    try:
        reply = chat(session_id=session_id, user_message=request.message)
        return ChatResponse(reply=reply, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.delete("/session/{session_id}", response_model=SessionClearResponse, tags=["Session"])
def clear_session(session_id: str):
    memory_manager.clear_session(session_id)
    return SessionClearResponse(message="Session cleared.", session_id=session_id)


@app.get("/session/{session_id}/history", tags=["Session"])
def get_history(session_id: str):
    history = memory_manager.get_history(session_id)
    return {"session_id": session_id, "history": history, "message_count": len(history)}
