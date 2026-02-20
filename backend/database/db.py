import sqlite3
import os

class Database:
    def __init__(self, db_path="migration_system.db"):
        self.db_path = db_path

    def execute(self, query, params=()):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
        finally:
            conn.close()

    def fetchall(self, query, params=()):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def fetchone(self, query, params=()):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def init_schema(self):
        """Initialize required tables including `feature_intent` and `repository_architecture`."""
        create_feature_intent = """
        CREATE TABLE IF NOT EXISTS feature_intent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_id TEXT UNIQUE,
            raw_model TEXT,
            normalized_model TEXT,
            enriched_model TEXT,
            intent_hash TEXT,
            extraction_version TEXT,
            llm_used INTEGER DEFAULT 0,
            validation_status TEXT,
            enrichment_status TEXT,
            enrichment_version TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_repo_arch = """
        CREATE TABLE IF NOT EXISTS repository_architecture (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            source_commit TEXT NOT NULL,
            language TEXT NOT NULL,
            framework TEXT NOT NULL,
            driver_model TEXT,
            driver_scope TEXT,
            base_test_class TEXT,
            inheritance_tree TEXT,        -- JSON
            execution TEXT,
            data_driven INTEGER DEFAULT 0,
            has_global_setup INTEGER DEFAULT 0,
            has_per_test_setup INTEGER DEFAULT 0,
            has_teardown INTEGER DEFAULT 0,
            config_files TEXT,            -- JSON array
            structure_type TEXT,
            
            -- Refined fields (JSON)
            driver_init_location TEXT,
            driver_teardown_location TEXT,
            driver_lifecycle_binding TEXT,
            parallel_config TEXT,
            data_provider TEXT,
            test_types_detected TEXT,
            framework_version TEXT,
            page_object_pattern TEXT,
            ui_architecture TEXT,
            api_architecture TEXT,

            architecture_hash TEXT,       -- deterministic hash of model
            analysis_version TEXT,        -- version of Step 10 logic
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(session_id, source_commit)
        );
        """

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(create_feature_intent)
            cursor.execute(create_repo_arch)
            
            # Migration: Add columns if they don't exist
            cursor.execute("PRAGMA table_info(feature_intent)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'enrichment_status' not in columns:
                cursor.execute("ALTER TABLE feature_intent ADD COLUMN enrichment_status TEXT")
            if 'enrichment_version' not in columns:
                cursor.execute("ALTER TABLE feature_intent ADD COLUMN enrichment_version TEXT")
            
            # Migration for repository_architecture
            cursor.execute("PRAGMA table_info(repository_architecture)")
            arch_columns = [info[1] for info in cursor.fetchall()]
            
            arch_migrations = [
                ('execution', "ALTER TABLE repository_architecture ADD COLUMN execution TEXT"),
                ('structure_type', "ALTER TABLE repository_architecture ADD COLUMN structure_type TEXT"),
                ('driver_init_location', "ALTER TABLE repository_architecture ADD COLUMN driver_init_location TEXT"),
                ('driver_teardown_location', "ALTER TABLE repository_architecture ADD COLUMN driver_teardown_location TEXT"),
                ('driver_lifecycle_binding', "ALTER TABLE repository_architecture ADD COLUMN driver_lifecycle_binding TEXT"),
                ('parallel_config', "ALTER TABLE repository_architecture ADD COLUMN parallel_config TEXT"),
                ('data_provider', "ALTER TABLE repository_architecture ADD COLUMN data_provider TEXT"),
                ('test_types_detected', "ALTER TABLE repository_architecture ADD COLUMN test_types_detected TEXT"),
                ('framework_version', "ALTER TABLE repository_architecture ADD COLUMN framework_version TEXT"),
                ('page_object_pattern', "ALTER TABLE repository_architecture ADD COLUMN page_object_pattern TEXT"),
                ('ui_architecture', "ALTER TABLE repository_architecture ADD COLUMN ui_architecture TEXT"),
                ('api_architecture', "ALTER TABLE repository_architecture ADD COLUMN api_architecture TEXT")
            ]
            
            for col_name, alter_sql in arch_migrations:
                if col_name not in arch_columns:
                    cursor.execute(alter_sql)
                
            conn.commit()
        finally:
            conn.close()
