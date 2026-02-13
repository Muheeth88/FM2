import uuid
import logging
from models import CreateSessionRequest, CreateSessionResponse
from database import get_db_connection

logger = logging.getLogger(__name__)

class SessionService:
    @staticmethod
    def create_session(request: CreateSessionRequest) -> CreateSessionResponse:
        # Validate inputs
        if not request.source_repo_url:
            raise ValueError("Source repository URL is required.")
        if not request.source_framework or not request.target_framework:
            raise ValueError("Source and target frameworks are required.")
        if request.source_framework == request.target_framework:
            # Although the user said any-to-any, usually you don't migrate to the same framework.
            # However, if they want to support it (e.g. version upgrade), we could allow it.
            # For now, let's keep it simple as per "Step 1 - Create Migration Session" in doc: "Ensure source != target"
            # Wait, the doc Step 1 says "Ensure source != target" for repo URL, but doesn't mention frameworks.
            # But usually it's good practice.
            pass

        session_id = str(uuid.uuid4())
        status = "CREATED"
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sessions (
                    id, source_repo_url, source_framework, target_framework, base_branch, pat, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                request.source_repo_url,
                request.source_framework,
                request.target_framework,
                request.base_branch,
                request.pat,
                status
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Session created and saved to DB: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to save session to DB: {str(e)}")
            raise RuntimeError(f"Database error: {str(e)}")
        
        return CreateSessionResponse(session_id=session_id, status=status)
