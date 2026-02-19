from fastapi import APIRouter, HTTPException
from models import (
    CreateSessionRequest, 
    CreateSessionResponse, 
    SelectFeaturesRequest, 
    CreateRunRequest, 
    MigrationRunResponse
)
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

@router.post("/select-features")
async def select_features(request: SelectFeaturesRequest):
    """
    Marks features as selected for migration.
    """
    try:
        success = SessionService.select_features(request)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update feature selection")
        return {"status": "SUCCESS", "message": f"Selected {len(request.feature_ids)} features"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error selecting features: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Selection failed: {str(e)}")

@router.post("/create-run", response_model=MigrationRunResponse)
async def create_migration_run(request: CreateRunRequest):
    """
    Starts an isolated migration run by creating a new git branch.
    """
    try:
        return SessionService.create_migration_run(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating migration run: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Run creation failed: {str(e)}")

@router.post("/{session_id}/bootstrap")
async def bootstrap_session(session_id: str):
    """
    Triggers the target repository bootstrap process.
    """
    try:
        return SessionService.bootstrap_target(session_id)
    except Exception as e:
        logger.error(f"Bootstrap failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
