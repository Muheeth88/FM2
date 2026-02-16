from fastapi import APIRouter, HTTPException
from services.repository_analyzer_service import RepositoryAnalyzerService
from services.feature_query_service import FeatureQueryService
from services.websocket_manager import ws_manager
from database.db import Database
from models import (
    AnalysisResponse, FeatureModel, JavaFileDependency, TestMethod,
    BuildDependency, DriverModel, AssertionModel, ConfigFileModel
)
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

@router.get("/{session_id}/features")
async def get_features(session_id: str):
    """
    Returns a summarized list of features for the UI table.
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
    results = get_analysis_data(session_id)
    if not results:
        raise HTTPException(status_code=404, detail="No analysis results found for this session.")
    return results

def get_analysis_data(session_id: str) -> AnalysisResponse:
    # Reconstruct AnalysisResponse from new tables
    session = db.fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))
    if not session:
        return None
    
    # 1. Features and Tests
    feature_rows = db.fetchall("SELECT * FROM features WHERE session_id = ?", (session_id,))
    features = []
    for f in feature_rows:
        test_rows = db.fetchall("SELECT * FROM tests WHERE feature_id = ?", (f["id"],))
        tests = [TestMethod(name=t["test_name"], annotations=eval(t["annotations"])) for t in test_rows]
        features.append(FeatureModel(
            feature_name=f["feature_name"],
            file_path=f["file_path"],
            tests=tests,
            lifecycle_hooks=eval(f["hooks"]) if f.get("hooks") else [],
            framework=f["framework"],
            language=f["language"]
        ))
    
    # 2. Dependency Graph
    nodes = db.fetchall("SELECT file_path, file_type, package_name FROM dependency_nodes WHERE session_id = ?", (session_id,))
    edges = db.fetchall("SELECT from_file, to_file FROM dependency_edges WHERE session_id = ?", (session_id,))
    
    dependency_graph = {}
    for node in nodes:
        file_path = node["file_path"]
        imports = [e["to_file"] for e in edges if e["from_file"] == file_path]
        dependency_graph[file_path] = JavaFileDependency(
            package=node["package_name"],
            imports=imports,
            class_name=file_path.split("/")[-1].split(".")[0] if "/" in file_path else file_path.split("\\")[-1].split(".")[0],
            type=node["file_type"]
        )
    
    # 3. Build Dependencies
    build_deps_rows = db.fetchall("SELECT name, version, type FROM build_dependencies WHERE session_id = ?", (session_id,))
    build_dependencies = [BuildDependency(**row) for row in build_deps_rows]

    # 4. Driver Model
    driver_row = db.fetchone("SELECT driver_type, initialization_pattern, thread_model FROM driver_model WHERE session_id = ?", (session_id,))
    driver_model = DriverModel(**driver_row) if driver_row else None

    # 5. Assertions
    assertion_rows = db.fetchall("SELECT file_path, assertion_type, library FROM assertions WHERE session_id = ?", (session_id,))
    assertions = [AssertionModel(**row) for row in assertion_rows]

    # 6. Config Files
    config_rows = db.fetchall("SELECT file_path, type FROM config_files WHERE session_id = ?", (session_id,))
    config_files = [ConfigFileModel(**row) for row in config_rows]

    # 7. Shared Modules
    shared_rows = db.fetchall("SELECT file_path FROM shared_modules WHERE session_id = ?", (session_id,))
    shared_modules = [row["file_path"] for row in shared_rows]

    return AnalysisResponse(
        session_id=session_id,
        repo_root=session["repo_root"],
        language=session["language"],
        framework=session["framework"],
        build_system=session["build_system"],
        dependency_graph=dependency_graph,
        features=features,
        build_dependencies=build_dependencies,
        driver_model=driver_model,
        assertions=assertions,
        config_files=config_files,
        shared_modules=shared_modules
    )
