from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.architecture.architecture_service import ArchitectureService
from database.db import Database
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/architecture", tags=["architecture"])
db = Database()
service = ArchitectureService(db)

class AnalyzeRequest(BaseModel):
    session_id: str

@router.post("/analyze")
async def analyze_architecture(request: AnalyzeRequest):
    """
    Triggers repository architecture analysis (Step 10).
    """
    try:
        result = service.analyze(request.session_id)
        if not result:
            raise HTTPException(status_code=404, detail="Session not found or analysis failed")
        return result
    except Exception as e:
        logger.error(f"Architecture analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}")
async def get_architecture(session_id: str):
    """
    Retrieves the latest architecture analysis for a session.
    """
    try:
        result = service.get_architecture(session_id)
        if not result:
            raise HTTPException(status_code=404, detail="No architecture analysis found for this session")
        return result
    except Exception as e:
        logger.error(f"Failed to fetch architecture: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
