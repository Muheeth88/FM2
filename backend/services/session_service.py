import uuid
import logging
from models import CreateSessionRequest, CreateSessionResponse
from database import get_db_connection
from services.workspace_service import WorkspaceService

logger = logging.getLogger(__name__)

from services.git_service import GitService

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
            logger.info("Executing STEP 1: DB Insert")
            # STEP 1: Insert session row in SQLite
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sessions (
                    id, name, source_repo_url, target_repo_url, source_framework, target_framework, base_branch, pat, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                request.name,
                request.source_repo_url,
                request.target_repo_url,
                request.source_framework,
                request.target_framework,
                request.base_branch,
                request.pat,
                status
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Session created and saved to DB: {session_id}")

            logger.info("Executing STEP 2: Workspace Init")
            # STEP 2: Initialize Workspace
            ws = WorkspaceService.initialize_workspace(session_id)
            
            logger.info("Executing STEP 3: Clone Source")
            # STEP 3: Clone Source Repository
            if not GitService.clone_repo(request.source_repo_url, ws["source_path"], request.pat, request.base_branch):
                logger.info("Clone with branch failed, trying default...")
                if not GitService.clone_repo(request.source_repo_url, ws["source_path"], request.pat):
                    raise RuntimeError("Failed to clone source repository.")
            
            source_commit = GitService.get_head_commit(ws["source_path"])
            
            # Update sessions.source_commit
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE sessions SET source_commit = ? WHERE id = ?", (source_commit, session_id))
            conn.commit()
            conn.close()
            logger.info(f"Source repo cloned. Commit: {source_commit}")

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
