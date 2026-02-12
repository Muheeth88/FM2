from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="QE Framework Migration System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import session

app.include_router(session.router)

@app.get("/")
async def root():
    return {"message": "QE Framework Migration System API is running"}
