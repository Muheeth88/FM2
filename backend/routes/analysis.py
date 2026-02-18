from fastapi import APIRouter, HTTPException
from services.repository_analyzer_service import RepositoryAnalyzerService
from services.feature_query_service import FeatureQueryService
from services.websocket_manager import ws_manager
from database.db import Database
from models import (
    AnalysisResponse, FeatureModel, JavaFileDependency, TestMethod,
    BuildDependency, DriverModel, AssertionModel, ConfigFileModel,
    FeatureSummaryResponse
)
from typing import List
import logging
import json
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sessions", tags=["sessions"])
db = Database()
service = RepositoryAnalyzerService(db, ws_manager)
query_service = FeatureQueryService(db)

@router.post("/{session_id}/analyze")
async def trigger_analysis(session_id: str):
    """
    Triggers full analysis using the new RepositoryAnalyzerService.
    Analysis runs as a background async task; progress is streamed via WebSocket.
    """
    try:
        session = db.fetchone("SELECT repo_root FROM sessions WHERE id = ?", (session_id,))
        if not session:
             raise HTTPException(status_code=404, detail="Session not found")
        
        repo_root = session["repo_root"]
        
        # Start as async background task (not blocking the response)
        task = asyncio.create_task(service.analyze(repo_root, session_id))
        
        # Ensure exceptions from the background task are logged
        def _on_task_done(t):
            if t.exception():
                logger.error(f"Analysis background task failed for session {session_id}: {t.exception()}")
        task.add_done_callback(_on_task_done)
        
        return {"session_id": session_id, "status": "ANALYZING"}
    except Exception as e:
        logger.error(f"Analysis trigger failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/status")
async def get_session_status(session_id: str):
    """
    Returns the current status of the session analysis.
    """
    session = db.fetchone("SELECT status FROM sessions WHERE id = ?", (session_id,))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "status": session["status"]}

@router.get("/{session_id}/features", response_model=List[FeatureSummaryResponse])
async def get_features(session_id: str):
    """
    Returns features with full file arrays (test_files, dependent_files, config_files, shared_modules).
    """
    return query_service.get_feature_summaries(session_id)

@router.get("/{session_id}/features/{feature_id}")
async def get_feature_detail(session_id: str, feature_id: str):
    """
    Returns full details for a specific feature.
    """
    detail = query_service.get_feature_detail(session_id, feature_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Feature details not found")
    return detail

@router.get("/{session_id}/full-analysis", response_model=AnalysisResponse)
async def get_analysis(session_id: str):
    """
    Retrieves existing full analysis results (original endpoint).
    """
    results = query_service.get_full_analysis(session_id)
    if not results:
        raise HTTPException(status_code=404, detail="No analysis results found for this session.")
    return results
