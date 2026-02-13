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
    """Initializes the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            source_repo_url TEXT NOT NULL,
            target_repo_url TEXT,
            source_framework TEXT NOT NULL,
            target_framework TEXT NOT NULL,
            base_branch TEXT NOT NULL,
            pat TEXT,
            status TEXT NOT NULL,
            source_commit TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create features table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS features (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            last_migrated_commit TEXT,
            validation_status TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")
