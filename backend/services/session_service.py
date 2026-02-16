import uuid
import logging
from models import CreateSessionRequest, CreateSessionResponse
from database import get_db_connection
from services.workspace_service import WorkspaceService
from services.git_service import GitService

logger = logging.getLogger(__name__)

class SessionService:
    @staticmethod
    def create_session(request: CreateSessionRequest) -> CreateSessionResponse:
        # Validate inputs
        if not request.source_repo_url:
            raise ValueError("Source repository URL is required.")
        if not request.source_framework or not request.target_framework:
            raise ValueError("Source and target frameworks are required.")

        session_id = str(uuid.uuid4())
        status = "CREATED"
        
        try:
            logger.info("Executing STEP 1: Workspace Init")
            # STEP 1: Initialize Workspace
            ws = WorkspaceService.initialize_workspace(session_id)
            repo_root = ws["source_path"]

            logger.info("Executing STEP 2: Clone Source")
            # STEP 2: Clone Source Repository
            if not GitService.clone_repo(request.source_repo_url, repo_root, request.pat, request.base_branch):
                logger.info("Clone with branch failed, trying default...")
                if not GitService.clone_repo(request.source_repo_url, repo_root, request.pat):
                    raise RuntimeError("Failed to clone source repository.")
            
            logger.info("Executing STEP 3: DB Insert")
            # STEP 3: Insert session row in SQLite
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # New schema: id, repo_root, language, framework, build_system
            cursor.execute('''
                INSERT INTO sessions (
                    id, repo_root, language, framework, build_system
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                session_id,
                repo_root,
                "unknown",
                request.source_framework,
                "unknown"
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Session created and saved to DB: {session_id}")

            logger.info("Executing STEP 4: Clone/Init Target")
            # STEP 4: Clone / Initialize Target Repository
            target_cloned = False
            if request.target_repo_url:
                logger.info(f"Attempting to clone target repo: {request.target_repo_url}")
                target_cloned = GitService.clone_repo(request.target_repo_url, ws["target_path"], request.pat)
            
            if not target_cloned:
                logger.info("Target repo not provided or clone failed. Initializing fresh repo.")
                GitService.init_repo(ws["target_path"])
            
            logger.info("Session initialization complete")
        except Exception as e:
            logger.error(f"Failed to complete session initialization: {str(e)}")
            raise RuntimeError(f"Initialization failed: {str(e)}")
        
        return CreateSessionResponse(session_id=session_id, status=status)
