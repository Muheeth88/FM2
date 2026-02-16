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
    
    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            repo_root TEXT,
            language TEXT,
            framework TEXT,
            build_system TEXT
        )
    ''')
    
    # Create features table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS features (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            feature_name TEXT,
            file_path TEXT,
            framework TEXT,
            language TEXT,
            hooks TEXT
        )
    ''')

    # Create tests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tests (
            id TEXT PRIMARY KEY,
            feature_id TEXT,
            test_name TEXT,
            annotations TEXT
        )
    ''')

    # Create dependency_nodes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dependency_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            file_path TEXT,
            file_type TEXT,
            package_name TEXT
        )
    ''')

    # Create dependency_edges table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dependency_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            from_file TEXT,
            to_file TEXT
        )
    ''')

    # Create build_dependencies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS build_dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            name TEXT,
            version TEXT,
            type TEXT
        )
    ''')

    # Create driver_model table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS driver_model (
            session_id TEXT PRIMARY KEY,
            driver_type TEXT,
            initialization_pattern TEXT,
            thread_model TEXT
        )
    ''')

    # Create assertions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assertions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            file_path TEXT,
            assertion_type TEXT,
            library TEXT
        )
    ''')

    # Create config_files table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            file_path TEXT,
            type TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully with the new schema.")
