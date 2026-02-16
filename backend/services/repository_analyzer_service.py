import uuid
from typing import Optional

from database.db import Database
from services.discovery.repo_discovery import RepoDiscovery
from services.framework_detection.framework_detector import FrameworkDetector
from services.build_metadata.build_extractor import BuildMetadataExtractor

from services.feature_extraction.extractor_factory import FeatureExtractorFactory
from services.dependency_analysis.analyzer_factory import DependencyAnalyzerFactory
from services.assertion_analysis.assertion_factory import AssertionDetectorFactory
from services.driver_analysis.driver_factory import DriverDetectorFactory
from services.config_scanner.config_scanner import ConfigScanner


class RepositoryAnalyzerService:

    def __init__(self, db: Database):
        self.db = db

    # ==========================
    # PUBLIC ENTRY POINT
    # ==========================
    def analyze(self, repo_root: str, session_id: Optional[str] = None) -> str:
        """
        Runs full repository analysis pipeline
        and persists results into SQLite.
        """

        session_id = session_id or str(uuid.uuid4())

        # --------------------------
        # 0. Clear Old Data
        # --------------------------
        self._clear_old_data(session_id)

        # --------------------------
        # 1. Repo Discovery
        # --------------------------
        language = RepoDiscovery.detect_language(repo_root)
        build_system = RepoDiscovery.detect_build_system(repo_root)
        framework = FrameworkDetector.detect(repo_root, language)

        self._insert_session(
            session_id,
            repo_root,
            language,
            framework,
            build_system
        )

        # --------------------------
        # 2. Build Metadata
        # --------------------------
        self._process_build_metadata(session_id, repo_root, build_system)

        # --------------------------
        # 3. Feature Extraction
        # --------------------------
        self._process_features(session_id, language, repo_root)

        # --------------------------
        # 4. Dependency Graph
        # --------------------------
        self._process_dependencies(session_id, language, repo_root)

        # --------------------------
        # 5. Assertions
        # --------------------------
        self._process_assertions(session_id, language, repo_root)

        # --------------------------
        # 6. Driver Model
        # --------------------------
        self._process_driver_model(session_id, language, repo_root)

        # --------------------------
        # 7. Config Files
        # --------------------------
        self._process_config_files(session_id, repo_root)

        return session_id

    # ==========================================================
    # INTERNAL PROCESSING METHODS
    # ==========================================================

    def _clear_old_data(self, session_id):
        """Removes existing analysis data for this session."""
        self.db.execute("DELETE FROM tests WHERE feature_id IN (SELECT id FROM features WHERE session_id = ?)", (session_id,))
        self.db.execute("DELETE FROM features WHERE session_id = ?", (session_id,))
        self.db.execute("DELETE FROM dependency_nodes WHERE session_id = ?", (session_id,))
        self.db.execute("DELETE FROM dependency_edges WHERE session_id = ?", (session_id,))
        self.db.execute("DELETE FROM build_dependencies WHERE session_id = ?", (session_id,))
        self.db.execute("DELETE FROM driver_model WHERE session_id = ?", (session_id,))
        self.db.execute("DELETE FROM assertions WHERE session_id = ?", (session_id,))
        self.db.execute("DELETE FROM config_files WHERE session_id = ?", (session_id,))

    def _insert_session(self, session_id, repo_root, language, framework, build_system):
        self.db.execute(
            "INSERT OR REPLACE INTO sessions VALUES (?, ?, ?, ?, ?)",
            (session_id, repo_root, language, framework, build_system)
        )

    # --------------------------
    # Build Metadata
    # --------------------------
    def _process_build_metadata(self, session_id, repo_root, build_system):
        dependencies = BuildMetadataExtractor.extract(repo_root, build_system)

        for dep in dependencies:
            self.db.execute(
                """
                INSERT INTO build_dependencies
                (session_id, name, version, type)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    dep.get("name"),
                    dep.get("version"),
                    dep.get("type")
                )
            )

    # --------------------------
    # Feature Extraction
    # --------------------------
    def _process_features(self, session_id, language, repo_root):
        extractor = FeatureExtractorFactory.get_extractor(language, repo_root)
        features = extractor.extract_features()

        for feature in features:
            feature_id = str(uuid.uuid4())

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
                    feature["file_path"],
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

    # --------------------------
    # Dependency Graph
    # --------------------------
    def _process_dependencies(self, session_id, language, repo_root):
        analyzer = DependencyAnalyzerFactory.get_analyzer(language, repo_root)
        results = analyzer.analyze()

        for file_path, data in results.items():

            self.db.execute(
                """
                INSERT INTO dependency_nodes
                (session_id, file_path, file_type, package_name)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session_id, 
                    file_path, 
                    data.get("type", "unknown"),
                    data.get("package")
                )
            )

            for dep in data.get("imports", []):
                self.db.execute(
                    """
                    INSERT INTO dependency_edges
                    (session_id, from_file, to_file)
                    VALUES (?, ?, ?)
                    """,
                    (session_id, file_path, dep)
                )

    # --------------------------
    # Assertion Detection
    # --------------------------
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

    # --------------------------
    # Driver Detection
    # --------------------------
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

    # --------------------------
    # Config File Scanner
    # --------------------------
    def _process_config_files(self, session_id, repo_root):
        configs = ConfigScanner.scan(repo_root)

        for c in configs:
            self.db.execute(
                """
                INSERT INTO config_files
                (session_id, file_path, type)
                VALUES (?, ?, ?)
                """,
                (
                    session_id,
                    c["file_path"],
                    c["type"]
                )
            )
