from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from database import init_db
from routes import git, sessions

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

@app.get("/")
async def root():
    return {"message": "QE Framework Migration System API is running"}
