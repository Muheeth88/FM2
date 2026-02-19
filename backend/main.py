from dotenv import load_dotenv
import os

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
from database import init_db
from routes import git, sessions, analysis, intent
from services.websocket_manager import ws_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
init_db()

app = FastAPI(title="QE Framework Migration System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(git.router)
app.include_router(sessions.router)
app.include_router(analysis.router)
app.include_router(intent.router)

@app.get("/")
async def root():
    return {"message": "QE Framework Migration System API is running"}

@app.websocket("/ws/sessions/{session_id}")
async def session_stream(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time analysis progress streaming."""
    print(f"WS connection attempt for session: {session_id}")
    try:
        await ws_manager.connect(session_id, websocket)
        print(f"WS connection accepted for session: {session_id}")
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"WS disconnected for session: {session_id}")
        ws_manager.disconnect(session_id)
    except Exception as e:
        print(f"WS error for session {session_id}: {str(e)}")
        ws_manager.disconnect(session_id)
