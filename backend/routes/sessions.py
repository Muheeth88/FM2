from fastapi import APIRouter, HTTPException
from models import CreateSessionRequest, CreateSessionResponse
from services.session_service import SessionService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/session", tags=["session"])

@router.post("", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """
    Creates a new migration session.
    """
    logger.info(f"Creating session for repo: {request.source_repo_url}")
    try:
        return SessionService.create_session(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while creating session")
