import uuid
import traceback
import asyncio
from datetime import datetime
from typing import Optional, Dict, Set, List

from database.db import Database
from services.discovery.repo_discovery import RepoDiscovery
from services.framework_detection.framework_detector import FrameworkDetector
from services.build_metadata.build_extractor import BuildMetadataExtractor

from services.feature_extraction.extractor_factory import FeatureExtractorFactory
from services.dependency_analysis.analyzer_factory import DependencyAnalyzerFactory
from services.assertion_analysis.assertion_factory import AssertionDetectorFactory
from services.driver_analysis.driver_factory import DriverDetectorFactory
from services.config_scanner.config_scanner import ConfigScanner

from services.dependency_graph.graph_builder import DependencyGraphBuilder
from services.dependency_graph.shared_module_detector import SharedModuleDetector

from services.feature_modeling.feature_closure_builder import FeatureClosureBuilder
from services.feature_modeling.feature_shared_mapper import FeatureSharedMapper
from services.feature_modeling.feature_config_mapper import FeatureConfigMapper
from services.feature_modeling.feature_hook_mapper import FeatureHookMapper

from services.ast_parsing.parser_factory import ASTParserFactory


import logging

logger = logging.getLogger(__name__)


class RepositoryAnalyzerService:

    def __init__(self, db: Database, ws_manager=None):
        self.db = db
        self.ws_manager = ws_manager

    # ==========================================================
    # PROGRESS EMISSION
    # ==========================================================

    async def _emit_progress(self, session_id: str, step: str, progress: int, message: str = None):
        """Emit progress to WebSocket client and update DB."""
        now = datetime.utcnow().isoformat()
        self.db.execute(
            "UPDATE sessions SET current_step=?, progress=?, updated_at=? WHERE id=?",
            (step, progress, now, session_id)
        )

        if self.ws_manager:
            await self.ws_manager.send(session_id, {
                "type": "progress",
                "session_id": session_id,
                "step": step,
                "progress": progress,
                "message": message or step
            })

    async def _emit_log(self, session_id: str, message: str):
        """Emit a log message to WebSocket client."""
        if self.ws_manager:
            await self.ws_manager.send(session_id, {
                "type": "log",
                "session_id": session_id,
                "message": message
            })

    async def _emit_error(self, session_id: str, error: str, trace: str):
        """Emit error to WebSocket client and update DB."""
        now = datetime.utcnow().isoformat()
        self.db.execute(
            "UPDATE sessions SET status='FAILED', error_message=?, error_trace=?, updated_at=? WHERE id=?",
            (error, trace, now, session_id)
        )

        if self.ws_manager:
            await self.ws_manager.send(session_id, {
                "type": "error",
                "session_id": session_id,
                "error": error,
                "trace": trace
            })

    async def _emit_complete(self, session_id: str):
        """Emit completion to WebSocket client."""
        if self.ws_manager:
            await self.ws_manager.send(session_id, {
                "type": "complete",
                "session_id": session_id,
                "step": "Complete",
                "progress": 100,
                "message": "Analysis completed successfully"
            })

    async def _emit_step_result(self, session_id: str, step: str, data: dict):
        """Emit detailed step result data to WebSocket client."""
        if self.ws_manager:
            await self.ws_manager.send(session_id, {
                "type": "step_result",
                "session_id": session_id,
                "step": step,
                "data": data
            })

    # ==========================================================
    # PUBLIC ENTRY POINT
    # ==========================================================

    async def analyze(self, repo_root: str, session_id: Optional[str] = None) -> str:
        session_id = session_id or str(uuid.uuid4())
        
        try:
            # 0. Set status to ANALYZING
            self.db.execute("UPDATE sessions SET status = 'ANALYZING' WHERE id = ?", (session_id,))
            
            # Tiny sleep to ensure WS connection from frontend is ready
            await asyncio.sleep(0.5)
            
            self._clear_old_data(session_id)

            # --------------------------
            # 1. Discovery
            # --------------------------
            await self._emit_progress(session_id, "Discovery", 5, "Detecting language, build system, and framework")
            language = RepoDiscovery.detect_language(repo_root)
            build_system = RepoDiscovery.detect_build_system(repo_root)
            framework = FrameworkDetector.detect(repo_root, language)
            await self._emit_log(session_id, f"Detected: {language} / {framework} / {build_system}")
            await self._emit_step_result(session_id, "Discovery", {
                "language": language,
                "framework": framework,
                "build_system": build_system
            })

            self._insert_session(session_id, repo_root, language, framework, build_system)

            # --------------------------
            # 2. Build Metadata
            # --------------------------
            await self._emit_progress(session_id, "Build Metadata", 15, "Extracting build dependencies")
            self._process_build_metadata(session_id, repo_root, build_system)
            build_dep_count = self.db.fetchone(
                "SELECT COUNT(*) as cnt FROM build_dependencies WHERE session_id = ?", (session_id,)
            )["cnt"]
            await self._emit_step_result(session_id, "Build Metadata", {
                "build_dependency_count": build_dep_count
            })

            # --------------------------
            # 3. Feature Extraction
            # --------------------------
            await self._emit_progress(session_id, "Feature Extraction", 25, "Scanning for test features")
            self._process_features(session_id, language, repo_root)
            feature_rows = self.db.fetchall(
                "SELECT feature_name, file_path FROM features WHERE session_id = ?", (session_id,)
            )
            await self._emit_step_result(session_id, "Feature Extraction", {
                "feature_count": len(feature_rows),
                "features": [{"name": f["feature_name"], "file": f["file_path"].split("/")[-1]} for f in feature_rows]
            })

            # --------------------------
            # 4. Dependency Analysis
            # --------------------------
            await self._emit_progress(session_id, "Dependency Analysis", 40, "Analyzing import dependencies")
            self._process_dependencies(session_id, language, repo_root)
            edge_count = self.db.fetchone(
                "SELECT COUNT(*) as cnt FROM dependency_edges WHERE session_id = ?", (session_id,)
            )["cnt"]
            node_count = self.db.fetchone(
                "SELECT COUNT(*) as cnt FROM dependency_nodes WHERE session_id = ?", (session_id,)
            )["cnt"]
            await self._emit_step_result(session_id, "Dependency Analysis", {
                "node_count": node_count,
                "edge_count": edge_count
            })

            # --------------------------
            # 5. Build Graph
            # --------------------------
            await self._emit_progress(session_id, "Build Graph", 50, "Building dependency graph")
            graph, reverse_graph = self._build_dependency_graph(session_id)
            await self._emit_step_result(session_id, "Build Graph", {
                "graph_nodes": len(graph),
                "reverse_graph_nodes": len(reverse_graph)
            })

            # --------------------------
            # 6. Shared Modules
            # --------------------------
            await self._emit_progress(session_id, "Shared Modules", 60, "Detecting shared modules")
            shared_modules = self._persist_shared_modules(session_id, reverse_graph)
            await self._emit_step_result(session_id, "Shared Modules", {
                "shared_module_count": len(shared_modules),
                "shared_modules": [s.split("/")[-1] for s in shared_modules]
            })

            # --------------------------
            # 7. Config Files
            # --------------------------
            await self._emit_progress(session_id, "Config Files", 70, "Scanning configuration files")
            config_files = self._process_config_files(session_id, repo_root)
            await self._emit_step_result(session_id, "Config Files", {
                "config_file_count": len(config_files),
                "config_files": [c.split("/")[-1] for c in config_files]
            })

            # --------------------------
            # 8. Feature Modeling
            # --------------------------
            await self._emit_progress(session_id, "Feature Modeling", 80, "Building feature dependency models")
            self._build_feature_models(
                session_id=session_id,
                repo_root=repo_root,
                language=language,
                graph=graph,
                shared_modules=shared_modules,
                config_files=config_files
            )
            # Query per-feature modeling results
            feature_model_summary = []
            for fr in feature_rows:
                fname = fr["feature_name"]
                dep_cnt = self.db.fetchone(
                    "SELECT COUNT(*) as cnt FROM feature_dependencies fd JOIN features f ON fd.feature_id = f.id WHERE f.feature_name = ? AND f.session_id = ?",
                    (fname, session_id)
                )["cnt"]
                shared_cnt = self.db.fetchone(
                    "SELECT COUNT(*) as cnt FROM feature_shared_modules fsm JOIN features f ON fsm.feature_id = f.id WHERE f.feature_name = ? AND f.session_id = ?",
                    (fname, session_id)
                )["cnt"]
                config_cnt = self.db.fetchone(
                    "SELECT COUNT(*) as cnt FROM feature_config_dependencies fcd JOIN features f ON fcd.feature_id = f.id WHERE f.feature_name = ? AND f.session_id = ?",
                    (fname, session_id)
                )["cnt"]
                feature_model_summary.append({
                    "feature": fname,
                    "dependencies": dep_cnt,
                    "shared_modules": shared_cnt,
                    "config_deps": config_cnt
                })
            await self._emit_step_result(session_id, "Feature Modeling", {
                "feature_models": feature_model_summary
            })

            # --------------------------
            # 9. Assertions
            # --------------------------
            await self._emit_progress(session_id, "Assertions", 90, "Detecting assertion patterns")
            self._process_assertions(session_id, language, repo_root)
            assertion_count = self.db.fetchone(
                "SELECT COUNT(*) as cnt FROM assertions WHERE session_id = ?", (session_id,)
            )["cnt"]
            await self._emit_step_result(session_id, "Assertions", {
                "assertion_count": assertion_count
            })

            # --------------------------
            # 10. Driver Model
            # --------------------------
            await self._emit_progress(session_id, "Driver Model", 95, "Detecting driver patterns")
            self._process_driver_model(session_id, language, repo_root)
            driver_row = self.db.fetchone(
                "SELECT driver_type, initialization_pattern, thread_model FROM driver_model WHERE session_id = ?", (session_id,)
            )
            await self._emit_step_result(session_id, "Driver Model", {
                "driver_type": driver_row["driver_type"] if driver_row else None,
                "initialization_pattern": driver_row["initialization_pattern"] if driver_row else None,
                "thread_model": driver_row["thread_model"] if driver_row else None
            })

            # FINAL: Set status to ANALYZED
            self.db.execute("UPDATE sessions SET status = 'ANALYZED', progress = 100 WHERE id = ?", (session_id,))
            await self._emit_complete(session_id)

        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            logger.error(f"Analysis failed for session {session_id}: {error_msg}\n{error_trace}")
            await self._emit_error(session_id, error_msg, error_trace)
            raise e

        return session_id

    # ==========================================================
    # CLEAR
    # ==========================================================

    def _clear_old_data(self, session_id):
        # Delete tests first (via feature_id, since tests table has no session_id)
        self.db.execute(
            "DELETE FROM tests WHERE feature_id IN (SELECT id FROM features WHERE session_id = ?)",
            (session_id,)
        )

        tables = [
            "features",
            "dependency_nodes",
            "dependency_edges",
            "build_dependencies",
            "driver_model",
            "assertions",
            "config_files",
            "shared_modules",
            "feature_dependencies",
            "feature_shared_modules",
            "feature_config_dependencies",
            "feature_hooks"
        ]

        for table in tables:
            self.db.execute(f"DELETE FROM {table} WHERE session_id = ?", (session_id,))

    # ==========================================================
    # SESSION
    # ==========================================================

    def _insert_session(self, session_id, repo_root, language, framework, build_system):
        self.db.execute(
            "INSERT OR REPLACE INTO sessions (id, repo_root, language, framework, build_system, status) VALUES (?, ?, ?, ?, ?, 'ANALYZING')",
            (session_id, repo_root, language, framework, build_system)
        )

    # ==========================================================
    # BUILD METADATA
    # ==========================================================

    def _process_build_metadata(self, session_id, repo_root, build_system):
        deps = BuildMetadataExtractor.extract(repo_root, build_system)

        for dep in deps:
            self.db.execute(
                """
                INSERT INTO build_dependencies
                (session_id, name, version, type)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, dep.get("name"), dep.get("version"), dep.get("type"))
            )

    # ==========================================================
    # FEATURES
    # ==========================================================

    def _process_features(self, session_id, language, repo_root):

        extractor = FeatureExtractorFactory.get_extractor(language, repo_root)
        features = extractor.extract_features()

        for feature in features:
            feature_id = str(uuid.uuid4())
            # Normalize path separators for consistency
            norm_path = feature["file_path"].replace("\\", "/")

            self.db.execute(
                """
                INSERT INTO features
                (id, session_id, feature_name, file_path, framework, language, hooks)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feature_id,
                    session_id,
                    feature["feature_name"],
                    norm_path,
                    feature["framework"],
                    feature["language"],
                    str(feature.get("lifecycle_hooks", []))
                )
            )

            for test in feature.get("tests", []):
                self.db.execute(
                    """
                    INSERT INTO tests
                    (id, feature_id, test_name, annotations)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        feature_id,
                        test["name"],
                        str(test.get("annotations", []))
                    )
                )

    # ==========================================================
    # DEPENDENCIES (WITH IMPORT NORMALIZER)
    # ==========================================================

    def _process_dependencies(self, session_id, language, repo_root):

        analyzer = DependencyAnalyzerFactory.get_analyzer(language, repo_root)
        results = analyzer.analyze()



        for file_path, data in results.items():
            # Normalize file_path separators
            norm_file_path = file_path.replace("\\", "/")

            self.db.execute(
                """
                INSERT INTO dependency_nodes
                (session_id, file_path, file_type, package_name)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    norm_file_path,
                    data.get("type", "unknown"),
                    data.get("package")
                )
            )

            raw_imports = data.get("imports", [])

            # All analyzers now resolve imports internally to absolute file paths.
            # We just normalize separators to forward slashes for cross-platform consistency.
            resolved_imports = [imp.replace("\\", "/") for imp in raw_imports]

            for dep in resolved_imports:
                self.db.execute(
                    """
                    INSERT INTO dependency_edges
                    (session_id, from_file, to_file)
                    VALUES (?, ?, ?)
                    """,
                    (session_id, norm_file_path, dep)
                )

    # ==========================================================
    # GRAPH
    # ==========================================================

    def _build_dependency_graph(self, session_id):

        rows = self.db.fetchall(
            "SELECT from_file, to_file FROM dependency_edges WHERE session_id = ?",
            (session_id,)
        )

        builder = DependencyGraphBuilder(rows)
        graph = builder.get_graph()
        reverse_graph = builder.get_reverse_graph()

        return graph, reverse_graph

    # ==========================================================
    # SHARED MODULES
    # ==========================================================

    def _persist_shared_modules(self, session_id, reverse_graph):

        detector = SharedModuleDetector(reverse_graph)
        shared = detector.detect_shared_modules()

        for file_path in shared:
            self.db.execute(
                "INSERT INTO shared_modules VALUES (?, ?)",
                (session_id, file_path)
            )

        return set(shared)

    # ==========================================================
    # CONFIG FILES
    # ==========================================================

    def _process_config_files(self, session_id, repo_root):

        configs = ConfigScanner.scan(repo_root)
        config_files = []

        for c in configs:
            # Normalize path separators for consistency
            norm_path = c["file_path"].replace("\\", "/")
            self.db.execute(
                """
                INSERT INTO config_files
                (session_id, file_path, type)
                VALUES (?, ?, ?)
                """,
                (session_id, norm_path, c["type"])
            )
            config_files.append(norm_path)

        return config_files

    # ==========================================================
    # FEATURE MODELING
    # ==========================================================

    def _build_feature_models(
        self,
        session_id: str,
        repo_root: str,
        language: str,
        graph: Dict[str, Set[str]],
        shared_modules: Set[str],
        config_files: List[str]
    ):

        feature_rows = self.db.fetchall(
            "SELECT id, file_path FROM features WHERE session_id = ?",
            (session_id,)
        )

        logger.info(f"[Feature Modeling] graph size={len(graph)}, features={len(feature_rows)}, shared_modules={len(shared_modules)}, config_files={len(config_files)}")

        closure_builder = FeatureClosureBuilder(graph)
        shared_mapper = FeatureSharedMapper(shared_modules)
        config_mapper = FeatureConfigMapper(config_files)

        ast_parser = ASTParserFactory.get_parser(language, repo_root)
        hook_mapper = FeatureHookMapper(ast_parser)

        for row in feature_rows:
            feature_id = row["id"]
            test_file = row["file_path"]

            closure = closure_builder.build_closure(test_file)

            for dep in closure:
                self.db.execute(
                    "INSERT INTO feature_dependencies (session_id, feature_id, file_path) VALUES (?, ?, ?)",
                    (session_id, feature_id, dep)
                )

            shared_for_feature = shared_mapper.map_feature_shared(closure)
            for s in shared_for_feature:
                self.db.execute(
                    "INSERT INTO feature_shared_modules (session_id, feature_id, file_path) VALUES (?, ?, ?)",
                    (session_id, feature_id, s)
                )

            config_for_feature = config_mapper.map_feature_configs(closure)
            for c in config_for_feature:
                self.db.execute(
                    "INSERT INTO feature_config_dependencies (session_id, feature_id, config_file) VALUES (?, ?, ?)",
                    (session_id, feature_id, c)
                )

            hooks = hook_mapper.collect_feature_hooks(
                [test_file] + list(closure)
            )

            for h in hooks:
                self.db.execute(
                    "INSERT INTO feature_hooks (session_id, feature_id, hook_data) VALUES (?, ?, ?)",
                    (session_id, feature_id, h)
                )

    # ==========================================================
    # ASSERTIONS
    # ==========================================================

    def _process_assertions(self, session_id, language, repo_root):

        detector = AssertionDetectorFactory.get_detector(language, repo_root)
        assertions = detector.detect_assertions()

        for a in assertions:
            self.db.execute(
                """
                INSERT INTO assertions
                (session_id, file_path, assertion_type, library)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    a["file_path"],
                    a["assertion_type"],
                    a["library"]
                )
            )

    # ==========================================================
    # DRIVER
    # ==========================================================

    def _process_driver_model(self, session_id, language, repo_root):

        detector = DriverDetectorFactory.get_detector(language, repo_root)
        driver_info = detector.detect_driver()

        self.db.execute(
            """
            INSERT INTO driver_model
            (session_id, driver_type, initialization_pattern, thread_model)
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                driver_info.get("driver_type"),
                driver_info.get("initialization_pattern"),
                driver_info.get("thread_model")
            )
        )
