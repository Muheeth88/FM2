import urllib.request
import urllib.error
import json
import os
import sqlite3

BASE_URL = "http://localhost:8000"
DB_PATH = "migration_system.db"

def make_request(url, method='POST', data=None):
    req = urllib.request.Request(url, method=method)
    if data:
        json_data = json.dumps(data).encode('utf-8')
        req.add_header('Content-Type', 'application/json')
        req.data = json_data
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode()}")
        return e.code, None
    except Exception as e:
        print(f"Request failed: {e}")
        return None, None

def test_cloning():
    payload = {
        "name": "Integration Test Session",
        "source_repo_url": "https://github.com/pytest-dev/pytest.git",
        "target_repo_url": "", # Test fresh target case
        "source_framework": "Selenium Python - Pytest",
        "target_framework": "Playwright Python - Pytest",
        "base_branch": "main"
    }
    
    print("Testing Step 3 & 4 (Cloning and Git Init)...")
    code, data = make_request(f"{BASE_URL}/api/session", "POST", payload)
    
    if code == 200 and data:
        session_id = data.get("session_id")
        print(f"Success! Session Created: {session_id}")
        
        # Verify DB
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row and row['source_commit']:
            print(f"DB Verified: Source Commit: {row['source_commit']}")
        else:
            print(f"Error: DB record missing or source_commit is null: {dict(row) if row else 'None'}")
            
        # Verify Filesystem
        ws_path = os.path.join(os.getcwd(), "workspaces", session_id)
        source_git = os.path.join(ws_path, "source", ".git")
        target_git = os.path.join(ws_path, "target", ".git")
        
        if os.path.exists(source_git):
            print(f"Source repo cloned successfully: {source_git}")
        else:
            print("Error: Source .git folder missing!")
            
        if os.path.exists(target_git):
            print(f"Target repo initialized/cloned successfully: {target_git}")
        else:
            print("Error: Target .git folder missing!")
            
    else:
        print(f"Error: API call failed with code {code}, data: {data}")

if __name__ == "__main__":
    test_cloning()
