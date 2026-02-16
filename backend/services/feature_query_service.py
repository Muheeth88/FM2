from typing import List, Dict, Optional
from database.db import Database

class FeatureQueryService:
    def __init__(self, db: Database):
        self.db = db

    def get_feature_summaries(self, session_id: str) -> List[Dict]:
        """
        Fetches a list of features with aggregated counts for dependencies,
        shared modules, and config dependencies.
        """
        query = """
        SELECT 
            f.id as feature_id,
            f.feature_name,
            f.status,
            f.last_migrated_commit,
            (SELECT COUNT(*) FROM feature_dependencies fd WHERE fd.feature_id = f.id) as dependent_file_count,
            (SELECT COUNT(*) FROM feature_config_dependencies fcd WHERE fcd.feature_id = f.id) as config_dependency_count,
            (SELECT COUNT(*) FROM feature_shared_modules fsm WHERE fsm.feature_id = f.id) as shared_module_count
        FROM features f
        WHERE f.session_id = ?
        """
        return self.db.fetchall(query, (session_id,))

    def get_feature_detail(self, session_id: str, feature_id: str) -> Optional[Dict]:
        """
        Fetches full details for a specific feature, including all dependency lists.
        """
        feature = self.db.fetchone("SELECT * FROM features WHERE id = ? AND session_id = ?", (feature_id, session_id))
        if not feature:
            return None

        # Fetch sub-data
        tests = self.db.fetchall("SELECT test_name, annotations FROM tests WHERE feature_id = ?", (feature_id,))
        dependencies = self.db.fetchall("SELECT file_path FROM feature_dependencies WHERE feature_id = ?", (feature_id,))
        shared_modules = self.db.fetchall("SELECT file_path FROM feature_shared_modules WHERE feature_id = ?", (feature_id,))
        configs = self.db.fetchall("SELECT config_file FROM feature_config_dependencies WHERE feature_id = ?", (feature_id,))
        hooks = self.db.fetchall("SELECT hook_data FROM feature_hooks WHERE feature_id = ?", (feature_id,))

        # Format arrays
        return {
            "feature_id": feature["id"],
            "feature_name": feature["feature_name"],
            "file_path": feature["file_path"],
            "status": feature["status"],
            "framework": feature["framework"],
            "language": feature["language"],
            "last_migrated_commit": feature["last_migrated_commit"],
            "tests": tests,
            "dependency_files": [d["file_path"] for d in dependencies],
            "shared_modules": [s["file_path"] for s in shared_modules],
            "config_dependencies": [c["config_file"] for c in configs],
            "hooks": [h["hook_data"] for h in hooks]
        }
