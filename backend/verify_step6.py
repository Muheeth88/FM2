import asyncio
import os
import sqlite3
import hashlib
import uuid
from database import init_db, get_db_connection
from services.repository_analyzer_service import RepositoryAnalyzerService

async def main():
    print("Initializing Database...")
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    session_id = str(uuid.uuid4())
    feature_id = str(uuid.uuid4())
    repo_root = "." # Dummy
    
    print(f"Creating Dummy Session: {session_id}")
    cursor.execute("INSERT INTO sessions (id, repo_root, status) VALUES (?, ?, ?)", (session_id, repo_root, 'ANALYZING'))
    
    print(f"Creating Dummy Feature: {feature_id}")
    file_hash = hashlib.sha256(b"test_content").hexdigest()
    cursor.execute("""
        INSERT INTO features (id, session_id, feature_name, file_path, file_hash, status) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (feature_id, session_id, "TestFeature", "tests/test_file.py", file_hash, "NOT_MIGRATED"))
    
    dep_hash = hashlib.sha256(b"dep_content").hexdigest()
    cursor.execute("""
        INSERT INTO feature_dependencies (session_id, feature_id, file_path, file_hash)
        VALUES (?, ?, ?, ?)
    """, (session_id, feature_id, "src/dep.py", dep_hash))
    
    conn.commit()
    
    analyzer = RepositoryAnalyzerService(None) # db is not used for execute if we mock it or pass it. 
    # Actually RepositoryAnalyzerService takes a Database object.
    from database.db import Database
    db = Database()
    analyzer = RepositoryAnalyzerService(db)
    
    print("Computing Snapshot Hash...")
    initial_hash = analyzer._compute_feature_snapshot_hash(feature_id)
    print(f"Initial Hash: {initial_hash}")
    
    # 1. Test NOT_MIGRATED (default)
    await analyzer._update_feature_statuses(session_id, repo_root)
    res = cursor.execute("SELECT status FROM features WHERE id = ?", (feature_id,)).fetchone()
    print(f"Status (No Snapshot): {res['status']}")
    assert res['status'] == 'NOT_MIGRATED'
    
    # 2. Test MIGRATED
    print("Creating Snapshot (MIGRATED test)...")
    cursor.execute("""
        INSERT INTO feature_snapshots (id, feature_id, session_id, source_commit, snapshot_hash)
        VALUES (?, ?, ?, ?, ?)
    """, (str(uuid.uuid4()), feature_id, session_id, "commit1", initial_hash))
    conn.commit()
    
    await analyzer._update_feature_statuses(session_id, repo_root)
    res = cursor.execute("SELECT status FROM features WHERE id = ?", (feature_id,)).fetchone()
    print(f"Status (Hashes match): {res['status']}")
    assert res['status'] == 'MIGRATED'
    
    # 3. Test NEEDS_UPDATE
    print("Modifying dependency (NEEDS_UPDATE test)...")
    new_dep_hash = hashlib.sha256(b"new_dep_content").hexdigest()
    cursor.execute("UPDATE feature_dependencies SET file_hash = ? WHERE feature_id = ?", (new_dep_hash, feature_id))
    conn.commit()
    
    await analyzer._update_feature_statuses(session_id, repo_root)
    res = cursor.execute("SELECT status FROM features WHERE id = ?", (feature_id,)).fetchone()
    print(f"Status (Hashes differ): {res['status']}")
    assert res['status'] == 'NEEDS_UPDATE'
    
    print("Verification Successful!")
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
