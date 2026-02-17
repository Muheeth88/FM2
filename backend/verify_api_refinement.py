import requests
import json

SESSION_ID = "c5b1c455-c" # Using the one from previous run or any existing one

def test_features_api():
    try:
        # We need a valid session ID from the DB to test this properly
        # Since I just ran verify_step6.py, I'll try to find a session
        import sqlite3
        conn = sqlite3.connect("migration_system.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        session = cursor.execute("SELECT id FROM sessions LIMIT 1").fetchone()
        if not session:
            print("No sessions found in DB. Run verify_step6.py first.")
            return
        
        session_id = session["id"]
        print(f"Testing features API for session: {session_id}")
        
        response = requests.get(f"http://localhost:8000/api/sessions/{session_id}/features")
        if response.status_code == 200:
            features = response.data if hasattr(response, 'data') else response.json()
            print(json.dumps(features[0] if features else {}, indent=2))
            
            # Check for new fields
            if features:
                f = features[0]
                required_fields = ["status", "dependent_count", "config_count", "shared_count"]
                for field in required_fields:
                    if field in f:
                        print(f"✅ Found field: {field} = {f[field]}")
                    else:
                        print(f"❌ Missing field: {field}")
        else:
            print(f"Failed to fetch features: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_features_api()
