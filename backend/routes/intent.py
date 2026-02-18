from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from services.intent_service import IntentService
from database.db import Database
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/intent", tags=["intent"])
db = Database()
service = IntentService(db)

class ProcessIntentRequest(BaseModel):
    session_id: str
    feature_ids: List[str]

@router.post("/process")
async def process_intents(request: ProcessIntentRequest):
    """
    Triggers intent extraction (Step 9) for selected features.
    """
    try:
        results = service.process_features(request.session_id, request.feature_ids)
        return {"session_id": request.session_id, "results": results}
    except Exception as e:
        logger.error(f"Intent processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}")
async def get_session_intents(session_id: str):
    """
    Retrieves all intent results for a session.
    """
    try:
        return service.get_session_intents(session_id)
    except Exception as e:
        logger.error(f"Failed to fetch session intents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
