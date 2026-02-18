from typing import List, Dict, Optional
from database.db import Database


class FeatureQueryService:
    def __init__(self, db: Database):
        self.db = db

    def get_feature_summaries(self, session_id: str) -> List[Dict]:
        """
        Returns features with their full file arrays (test_files, dependent_files,
        config_files, shared_modules), each as {path, hash} objects.
        """
        features = self.db.fetchall(
            "SELECT id, feature_name, file_path, file_hash, status, last_migrated_commit FROM features WHERE session_id = ?",
            (session_id,)
        )

        result = []
        for f in features:
            feature_id = f["id"]

            # Test files: the feature's own test file
            test_files = [{"path": f["file_path"], "hash": f["file_hash"]}]

            # Dependent files
            deps = self.db.fetchall(
                "SELECT file_path, file_hash FROM feature_dependencies WHERE feature_id = ?",
                (feature_id,)
            )
            dependent_files = [{"path": d["file_path"], "hash": d["file_hash"]} for d in deps]

            # Config files
            configs = self.db.fetchall(
                "SELECT config_file, file_hash FROM feature_config_dependencies WHERE feature_id = ?",
                (feature_id,)
            )
            config_files = [{"path": c["config_file"], "hash": c["file_hash"]} for c in configs]

            # Shared modules
            shared = self.db.fetchall(
                "SELECT file_path, file_hash FROM feature_shared_modules WHERE feature_id = ?",
                (feature_id,)
            )
            shared_modules = [{"path": s["file_path"], "hash": s["file_hash"]} for s in shared]

            result.append({
                "feature_id": feature_id,
                "name": f["feature_name"],
                "status": f.get("status", "NOT_MIGRATED"),
                "last_migrated": f.get("last_migrated_commit"),
                "dependent_count": len(dependent_files),
                "config_count": len(config_files),
                "shared_count": len(shared_modules),
                "test_files": test_files,
                "dependent_files": dependent_files,
                "config_files": config_files,
                "shared_modules": shared_modules,
            })

        return result

    def get_feature_detail(self, session_id: str, feature_id: str) -> Optional[Dict]:
        """
        Fetches full details for a specific feature, including all dependency lists.
        """
        feature = self.db.fetchone("SELECT * FROM features WHERE id = ? AND session_id = ?", (feature_id, session_id))
        if not feature:
            return None

        # Fetch sub-data
        test_rows = self.db.fetchall("SELECT test_name, annotations FROM tests WHERE feature_id = ?", (feature_id,))
        tests = []
        for t in test_rows:
            try:
                annos = eval(t["annotations"]) if t["annotations"] else []
            except:
                annos = []
            tests.append({"name": t["test_name"], "annotations": annos})

        dependencies = self.db.fetchall("SELECT file_path, file_hash FROM feature_dependencies WHERE feature_id = ?", (feature_id,))
        shared_modules = self.db.fetchall("SELECT file_path, file_hash FROM feature_shared_modules WHERE feature_id = ?", (feature_id,))
        configs = self.db.fetchall("SELECT config_file, file_hash FROM feature_config_dependencies WHERE feature_id = ?", (feature_id,))
        hooks = self.db.fetchall("SELECT hook_data FROM feature_hooks WHERE feature_id = ?", (feature_id,))

        return {
            "feature_id": feature["id"],
            "feature_name": feature["feature_name"],
            "file_path": feature["file_path"],
            "file_hash": feature["file_hash"],
            "status": feature.get("status"),
            "framework": feature["framework"],
            "language": feature["language"],
            "last_migrated_commit": feature.get("last_migrated_commit"),
            "tests": tests,
            "dependency_files": [{"path": d["file_path"], "hash": d["file_hash"]} for d in dependencies],
            "shared_modules": [{"path": s["file_path"], "hash": s["file_hash"]} for s in shared_modules],
            "config_dependencies": [{"path": c["config_file"], "hash": c["file_hash"]} for c in configs],
            "hooks": [h["hook_data"] for h in hooks]
        }

    def get_full_analysis(self, session_id: str) -> Optional[Dict]:
        """
        Retrieves existing full analysis results (dependency graph, build deps, driver, etc).
        """
        session = self.db.fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))
        if not session:
            return None
        
        # 1. Features
        feature_summaries = self.get_feature_summaries(session_id)
        
        # 2. Dependency Graph
        nodes = self.db.fetchall("SELECT file_path, file_type, package_name FROM dependency_nodes WHERE session_id = ?", (session_id,))
        edges = self.db.fetchall("SELECT from_file, to_file FROM dependency_edges WHERE session_id = ?", (session_id,))
        
        dependency_graph = {}
        for node in nodes:
            file_path = node["file_path"]
            imports = [e["to_file"] for e in edges if e["from_file"] == file_path]
            dependency_graph[file_path] = {
                "package": node["package_name"],
                "imports": imports,
                "class_name": file_path.split("/")[-1].split(".")[0],
                "type": node["file_type"]
            }
        
        # 3. Build Dependencies
        build_dependencies = self.db.fetchall("SELECT name, version, type FROM build_dependencies WHERE session_id = ?", (session_id,))

        # 4. Driver Model
        driver_model = self.db.fetchone("SELECT driver_type, initialization_pattern, thread_model FROM driver_model WHERE session_id = ?", (session_id,))

        # 5. Assertions
        assertions = self.db.fetchall("SELECT file_path, assertion_type, library FROM assertions WHERE session_id = ?", (session_id,))

        # 6. Config Files
        config_files = self.db.fetchall("SELECT file_path, type FROM config_files WHERE session_id = ?", (session_id,))

        # 7. Shared Modules
        shared_modules = self.db.fetchall("SELECT file_path FROM shared_modules WHERE session_id = ?", (session_id,))

        return {
            "session_id": session_id,
            "repo_root": session["repo_root"],
            "language": session["language"],
            "framework": session["framework"],
            "build_system": session["build_system"],
            "dependency_graph": dependency_graph,
            "features": feature_summaries,
            "build_dependencies": build_dependencies,
            "driver_model": driver_model,
            "assertions": assertions,
            "config_files": config_files,
            "shared_modules": [row["file_path"] for row in shared_modules]
        }
