import logging
import json
import hashlib
import os
from datetime import datetime
from typing import Optional, Dict, Any

from database.db import Database
from services.architecture.analyzer_factory import ArchitectureAnalyzerFactory
from services.git_service import GitService

logger = logging.getLogger(__name__)

class ArchitectureService:
    def __init__(self, db: Database):
        self.db = db
        self.version = "1.0.0"

    def analyze(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Performs architecture analysis (Step 10) for a session.
        """
        # 1. Fetch session details
        session = self.db.fetchone(
            "SELECT repo_root, language, framework FROM sessions WHERE id = ?",
            (session_id,)
        )

        if not session:
            logger.error(f"Session {session_id} not found")
            return None

        repo_root = session["repo_root"]
        language = session["language"]
        
        if not repo_root or not os.path.exists(repo_root):
            logger.error(f"Repository root not found: {repo_root}")
            raise Exception(f"Repository root not found: {repo_root}")

        # 2. Get current commit
        source_commit = GitService.get_head_commit(repo_root) or "unknown"

        # 3. Perform analysis using factory
        logger.info(f"Starting architecture analysis for session {session_id} (Language: {language})")
        analyzer = ArchitectureAnalyzerFactory.get_analyzer(language)
        model = analyzer.analyze(repo_root)

        # 4. Generate architecture hash (deterministic)
        arch_hash = self._compute_architecture_hash(model)

        # 5. Prepare data for persistence
        arch_data = {
            "session_id": session_id,
            "source_commit": source_commit,
            "language": model.language,
            "framework": model.framework,
            "driver_model": model.driver_model,
            "driver_scope": model.driver_scope,
            "base_test_class": model.base_test_class,
            "inheritance_tree": json.dumps(model.inheritance_tree) if model.inheritance_tree is not None else None,
            "execution": json.dumps(model.execution) if model.execution is not None else None,
            "data_driven": 1 if model.data_driven is True else (0 if model.data_driven is False else None),
            "has_global_setup": 1 if model.has_global_setup is True else (0 if model.has_global_setup is False else None),
            "has_per_test_setup": 1 if model.has_per_test_setup is True else (0 if model.has_per_test_setup is False else None),
            "has_teardown": 1 if model.has_teardown is True else (0 if model.has_teardown is False else None),
            "config_files": json.dumps(model.config_files) if model.config_files is not None else None,
            "structure_type": model.structure_type,

            # Refined fields (v1.2.0)
            "driver_init_location": json.dumps(model.driver_init_location) if model.driver_init_location is not None else None,
            "driver_teardown_location": json.dumps(model.driver_teardown_location) if model.driver_teardown_location is not None else None,
            "driver_lifecycle_binding": json.dumps(model.driver_lifecycle_binding) if model.driver_lifecycle_binding is not None else None,
            "parallel_config": json.dumps(model.parallel_config) if model.parallel_config is not None else None,
            "data_provider": json.dumps(model.data_provider) if model.data_provider is not None else None,
            "test_types_detected": json.dumps(model.test_types_detected) if model.test_types_detected is not None else None,
            "framework_version": json.dumps(model.framework_version) if model.framework_version is not None else None,
            "page_object_pattern": json.dumps(model.page_object_pattern) if model.page_object_pattern is not None else None,
            "ui_architecture": json.dumps(model.ui_architecture) if model.ui_architecture is not None else None,
            "api_architecture": json.dumps(model.api_architecture) if model.api_architecture is not None else None,

            "architecture_hash": arch_hash,
            "analysis_version": model.analysis_version,
            "updated_at": datetime.utcnow().isoformat()
        }

        # 6. Persist to database
        self._persist_architecture(arch_data)
        
        logger.info(f"Architecture analysis completed for session {session_id}")
        
        # Print for immediate debug visibility in terminal
        print(f"DEBUG: ArchitectureService.analyze returning {len(str(arch_data))} bytes of data")
        
        return arch_data

    def _compute_architecture_hash(self, model) -> str:
        """Computes a deterministic hash of the architecture model."""
        data = {
            "driver_model": model.driver_model,
            "driver_scope": model.driver_scope,
            "base_test_class": model.base_test_class,
            "inheritance_tree": model.inheritance_tree,
            "data_driven": model.data_driven,
            "has_global_setup": model.has_global_setup,
            "has_per_test_setup": model.has_per_test_setup,
            "has_teardown": model.has_teardown,
            "config_files": sorted(model.config_files) if model.config_files else [],
            "page_object_pattern": model.page_object_pattern,
            "execution": model.execution
        }
        encoded = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()

    def _persist_architecture(self, data: Dict[str, Any]):
        """Inserts or updates architecture analysis results."""
        logger.info(f"Persisting architecture data for session {data['session_id']}")
        logger.debug(f"Data: {json.dumps(data, indent=2)}")
        query = """
        INSERT INTO repository_architecture (
            session_id, source_commit, language, framework,
            driver_model, driver_scope, base_test_class, inheritance_tree,
            execution, data_driven, has_global_setup, has_per_test_setup,
            has_teardown, config_files, structure_type, 
            driver_init_location, driver_teardown_location, driver_lifecycle_binding,
            parallel_config, data_provider, test_types_detected, 
            framework_version, page_object_pattern, ui_architecture, api_architecture,
            architecture_hash, analysis_version, updated_at, created_at
        ) VALUES (
            :session_id, :source_commit, :language, :framework,
            :driver_model, :driver_scope, :base_test_class, :inheritance_tree,
            :execution, :data_driven, :has_global_setup, :has_per_test_setup,
            :has_teardown, :config_files, :structure_type,
            :driver_init_location, :driver_teardown_location, :driver_lifecycle_binding,
            :parallel_config, :data_provider, :test_types_detected, 
            :framework_version, :page_object_pattern, :ui_architecture, :api_architecture,
            :architecture_hash, :analysis_version, :updated_at, :updated_at
        )
        ON CONFLICT(session_id, source_commit) DO UPDATE SET
            language=excluded.language,
            framework=excluded.framework,
            driver_model=excluded.driver_model,
            driver_scope=excluded.driver_scope,
            base_test_class=excluded.base_test_class,
            inheritance_tree=excluded.inheritance_tree,
            execution=excluded.execution,
            data_driven=excluded.data_driven,
            has_global_setup=excluded.has_global_setup,
            has_per_test_setup=excluded.has_per_test_setup,
            has_teardown=excluded.has_teardown,
            config_files=excluded.config_files,
            structure_type=excluded.structure_type,
            driver_init_location=excluded.driver_init_location,
            driver_teardown_location=excluded.driver_teardown_location,
            driver_lifecycle_binding=excluded.driver_lifecycle_binding,
            parallel_config=excluded.parallel_config,
            data_provider=excluded.data_provider,
            test_types_detected=excluded.test_types_detected,
            framework_version=excluded.framework_version,
            page_object_pattern=excluded.page_object_pattern,
            ui_architecture=excluded.ui_architecture,
            api_architecture=excluded.api_architecture,
            architecture_hash=excluded.architecture_hash,
            analysis_version=excluded.analysis_version,
            updated_at=excluded.updated_at
        """
        try:
            self.db.execute(query, data)
            logger.info("Database persistence successful")
        except Exception as e:
            logger.error(f"Database persistence failed: {str(e)}")
            raise e


    def get_architecture(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the latest architecture analysis for a session."""
        return self.db.fetchone(
            "SELECT * FROM repository_architecture WHERE session_id = ? ORDER BY updated_at DESC LIMIT 1",
            (session_id,)
        )
