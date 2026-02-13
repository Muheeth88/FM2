import urllib.request
import json
import os
import time

BASE_URL = "http://localhost:8000"

def make_request(url, method='POST', data=None):
    req = urllib.request.Request(url, method=method)
    if data:
        json_data = json.dumps(data).encode('utf-8')
        req.add_header('Content-Type', 'application/json')
        req.data = json_data
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except Exception as e:
        print(f"Request failed: {e}")
        return None, None

def test_initiate_migration():
    payload = {
        "source_repo_url": "https://github.com/pytest-dev/pytest.git",
        "source_framework": "Selenium Python - Pytest",
        "target_framework": "Playwright Python - Pytest",
        "base_branch": "main"
    }
    
    print("Testing Initiate Migration (Session + Workspace)...")
    code, data = make_request(f"{BASE_URL}/api/session", "POST", payload)
    
    if code == 200 and data:
        session_id = data.get("session_id")
        print(f"Success! Session Created: {session_id}")
        
        # Check if workspace folders exist
        # Workspace is in d:\Workspace\FM2\backend\workspaces
        ws_path = os.path.join(os.getcwd(), "workspaces", session_id)
        source_path = os.path.join(ws_path, "source")
        target_path = os.path.join(ws_path, "target")
        
        if os.path.exists(source_path) and os.path.exists(target_path):
            print(f"Workspace folders verified: {ws_path}")
        else:
            print(f"Error: Workspace folders NOT found at {ws_path}")
    else:
        print(f"Error: API call failed with code {code}, data: {data}")

if __name__ == "__main__":
    test_initiate_migration()
