import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Base directory for all migration workspaces
BASE_WORKSPACE_DIR = Path(__file__).parent.parent / "workspaces"

class WorkspaceService:
    @staticmethod
    def initialize_workspace(session_id: str) -> dict:
        """
        Creates the workspace folder structure:
        /workspace/{session_id}/source
        /workspace/{session_id}/target
        """
        session_path = BASE_WORKSPACE_DIR / session_id
        source_path = session_path / "source"
        target_path = session_path / "target"

        try:
            # Create directories
            os.makedirs(source_path, exist_ok=True)
            os.makedirs(target_path, exist_ok=True)
            
            # Validate permissions/existence
            if not source_path.exists() or not target_path.exists():
                raise RuntimeError("Failed to create workspace directories.")
            
            logger.info(f"Workspace initialized for session {session_id} at {session_path}")
            
            return {
                "session_path": str(session_path),
                "source_path": str(source_path),
                "target_path": str(target_path)
            }
        except Exception as e:
            logger.error(f"Error initializing workspace for session {session_id}: {str(e)}")
            raise RuntimeError(f"Workspace initialization failed: {str(e)}")

    @staticmethod
    def get_session_path(session_id: str) -> Path:
        return BASE_WORKSPACE_DIR / session_id
