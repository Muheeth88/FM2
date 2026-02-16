from fastapi import APIRouter, HTTPException
from services.repository_analyzer_service import RepositoryAnalyzerService
from database.db import Database
from models import (
    AnalysisResponse, FeatureModel, JavaFileDependency, TestMethod,
    BuildDependency, DriverModel, AssertionModel, ConfigFileModel
)
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])
db = Database()
service = RepositoryAnalyzerService(db)

@router.post("/{session_id}", response_model=AnalysisResponse)
async def trigger_analysis(session_id: str):
    """
    Triggers full analysis using the new RepositoryAnalyzerService.
    """
    try:
        # We need repo_root. For now, let's assume it's in the sessions table.
        session = db.fetchone("SELECT repo_root FROM sessions WHERE id = ?", (session_id,))
        if not session:
             raise HTTPException(status_code=404, detail="Session not found")
        
        repo_root = session["repo_root"]
        service.analyze(repo_root, session_id)
        
        return get_analysis_data(session_id)
    except Exception as e:
        logger.error(f"Analysis trigger failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}", response_model=AnalysisResponse)
async def get_analysis(session_id: str):
    """
    Retrieves existing analysis results.
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
        config_files=config_files
    )
