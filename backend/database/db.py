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
        """Initialize required tables including `feature_intent`."""
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
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(create_feature_intent)
            
            # Migration: Add columns if they don't exist
            cursor.execute("PRAGMA table_info(feature_intent)")
            columns = [info[1] for info in cursor.fetchall()]
            
            if 'enrichment_status' not in columns:
                cursor.execute("ALTER TABLE feature_intent ADD COLUMN enrichment_status TEXT")
            if 'enrichment_version' not in columns:
                cursor.execute("ALTER TABLE feature_intent ADD COLUMN enrichment_version TEXT")
                
            conn.commit()
        finally:
            conn.close()
