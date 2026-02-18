from typing import List, Dict, Any
import logging
import os
import glob
from services.intent_extractor_service import IntentExtractorService
from database.db import Database

logger = logging.getLogger(__name__)

class IntentService:
    def __init__(self, db: Database):
        self.db = db
        self.extractor_service = IntentExtractorService(db_path=db.db_path)

    def process_features(self, session_id: str, feature_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Processes intent extraction for a list of features.
        Discovers all workspace .java files for cross-file Page Object resolution.
        """
        # Discover workspace root and all Java files for cross-file resolution
        workspace_root = self._find_workspace_root(session_id)
        workspace_files = self._discover_java_files(workspace_root) if workspace_root else []
        logger.info(f"Discovered {len(workspace_files)} Java files in workspace for cross-file resolution")

        results = []
        for feature_id in feature_ids:
            try:
                # Get feature detail to find the file path
                feature = self.db.fetchone(
                    "SELECT file_path FROM features WHERE id = ? AND session_id = ?",
                    (feature_id, session_id)
                )

                if not feature:
                    logger.warning(f"Feature {feature_id} not found in session {session_id}")
                    continue

                file_path = feature["file_path"]

                # Full Step 9 pipeline with cross-file resolution
                result = self.extractor_service.process_feature(
                    session_id=session_id,
                    feature_id=feature_id,
                    file_paths=[file_path],
                    workspace_files=workspace_files
                )
                results.append(result)

            except Exception as e:
                logger.error(f"Failed to process intent for feature {feature_id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                # We continue with other features even if one fails

        return results

    def _find_workspace_root(self, session_id: str) -> str:
        """Find the workspace root directory for a session."""
        # Check for the source directory under the session workspace
        workspace_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'workspaces', session_id, 'source'
        )
        if os.path.isdir(workspace_dir):
            return workspace_dir

        # Fallback: try without 'source' subdirectory
        workspace_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'workspaces', session_id
        )
        if os.path.isdir(workspace_dir):
            return workspace_dir

        logger.warning(f"Workspace root not found for session {session_id}")
        return None

    def _discover_java_files(self, workspace_root: str) -> List[str]:
        """Discover all .java files in the workspace."""
        if not workspace_root:
            return []

        java_files = []
        for root, dirs, files in os.walk(workspace_root):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', 'target', 'build', '.gradle')]
            for f in files:
                if f.endswith('.java'):
                    java_files.append(os.path.join(root, f))

        return java_files

    def get_session_intents(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all intent results for a given session.
        Joins with features table to get feature name.
        """
        query = """
            SELECT fi.*, f.feature_name 
            FROM feature_intent fi
            JOIN features f ON fi.feature_id = f.id
            WHERE f.session_id = ?
        """
        rows = self.db.fetchall(query, (session_id,))
        return rows
