import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = "migration_system.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database with required tables using the new schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tables = [
        ('''CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            repo_root TEXT,
            language TEXT,
            framework TEXT,
            build_system TEXT,
            status TEXT DEFAULT 'PENDING',
            current_step TEXT,
            progress INTEGER DEFAULT 0,
            error_message TEXT,
            error_trace TEXT,
            updated_at TIMESTAMP
        )''', "sessions"),
        ('''CREATE TABLE IF NOT EXISTS features (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            feature_name TEXT,
            file_path TEXT,
            file_hash TEXT,
            framework TEXT,
            language TEXT,
            hooks TEXT,
            status TEXT DEFAULT 'NOT_MIGRATED',
            last_migrated_commit TEXT
        )''', "features"),
        ('''CREATE TABLE IF NOT EXISTS tests (
            id TEXT PRIMARY KEY,
            feature_id TEXT,
            test_name TEXT,
            annotations TEXT
        )''', "tests"),
        ('''CREATE TABLE IF NOT EXISTS dependency_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            file_path TEXT,
            file_type TEXT,
            package_name TEXT
        )''', "dependency_nodes"),
        ('''CREATE TABLE IF NOT EXISTS dependency_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            from_file TEXT,
            to_file TEXT
        )''', "dependency_edges"),
        ('''CREATE TABLE IF NOT EXISTS build_dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            name TEXT,
            version TEXT,
            type TEXT
        )''', "build_dependencies"),
        ('''CREATE TABLE IF NOT EXISTS driver_model (
            session_id TEXT PRIMARY KEY,
            driver_type TEXT,
            initialization_pattern TEXT,
            thread_model TEXT
        )''', "driver_model"),
        ('''CREATE TABLE IF NOT EXISTS assertions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            file_path TEXT,
            assertion_type TEXT,
            library TEXT
        )''', "assertions"),
        ('''CREATE TABLE IF NOT EXISTS config_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            file_path TEXT,
            type TEXT
        )''', "config_files"),
        ('''CREATE TABLE IF NOT EXISTS shared_modules (
            session_id TEXT,
            file_path TEXT
        )''', "shared_modules"),
        ('''CREATE TABLE IF NOT EXISTS feature_dependencies (
            feature_id TEXT,
            session_id TEXT,
            file_path TEXT,
            file_hash TEXT
        )''', "feature_dependencies"),
        ('''CREATE TABLE IF NOT EXISTS feature_shared_modules (
            feature_id TEXT,
            session_id TEXT,
            file_path TEXT,
            file_hash TEXT
        )''', "feature_shared_modules"),
        ('''CREATE TABLE IF NOT EXISTS feature_config_dependencies (
            feature_id TEXT,
            session_id TEXT,
            config_file TEXT,
            file_hash TEXT
        )''', "feature_config_dependencies"),
        ('''CREATE TABLE IF NOT EXISTS feature_hooks (
            feature_id TEXT,
            session_id TEXT,
            hook_data TEXT
        )''', "feature_hooks"),
        ('''CREATE TABLE IF NOT EXISTS feature_snapshots (
            id TEXT PRIMARY KEY,
            feature_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            source_commit TEXT NOT NULL,
            snapshot_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''', "feature_snapshots")
    ]

    for sql, name in tables:
        try:
            cursor.execute(sql)
            logger.info(f"Verified/Created table: {name}")
        except Exception as e:
            logger.error(f"Error creating table {name}: {e}")

    # Migrations: Add new columns if they don't exist
    migrations = [
        ("ALTER TABLE sessions ADD COLUMN status TEXT DEFAULT 'PENDING'", "sessions.status"),
        ("ALTER TABLE sessions ADD COLUMN current_step TEXT", "sessions.current_step"),
        ("ALTER TABLE sessions ADD COLUMN progress INTEGER DEFAULT 0", "sessions.progress"),
        ("ALTER TABLE sessions ADD COLUMN error_message TEXT", "sessions.error_message"),
        ("ALTER TABLE sessions ADD COLUMN error_trace TEXT", "sessions.error_trace"),
        ("ALTER TABLE sessions ADD COLUMN updated_at TIMESTAMP", "sessions.updated_at"),
        ("ALTER TABLE features ADD COLUMN status TEXT DEFAULT 'NOT_MIGRATED'", "features.status"),
        ("ALTER TABLE features ADD COLUMN last_migrated_commit TEXT", "features.last_migrated_commit"),
        ("ALTER TABLE features ADD COLUMN hooks TEXT", "features.hooks"),
        ("ALTER TABLE dependency_nodes ADD COLUMN package_name TEXT", "dependency_nodes.package_name"),
        ("ALTER TABLE features ADD COLUMN file_hash TEXT", "features.file_hash"),
        ("ALTER TABLE feature_dependencies ADD COLUMN file_hash TEXT", "feature_dependencies.file_hash"),
        ("ALTER TABLE feature_shared_modules ADD COLUMN file_hash TEXT", "feature_shared_modules.file_hash"),
        ("ALTER TABLE feature_config_dependencies ADD COLUMN file_hash TEXT", "feature_config_dependencies.file_hash"),
        ("ALTER TABLE features ADD COLUMN snapshot_hash TEXT", "features.snapshot_hash"),
        ("ALTER TABLE features ADD COLUMN source_commit TEXT", "features.source_commit")
    ]

    for sql, name in migrations:
        try:
            cursor.execute(sql)
            logger.info(f"Migration successful: {name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass # Already exists
            else:
                logger.warning(f"Migration skipped/failed for {name}: {e}")

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")
