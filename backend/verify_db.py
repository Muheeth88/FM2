from database.db import Database
from database import init_db

# Ensure migrations run
init_db()

db = Database()
try:
    session = db.fetchone("SELECT id FROM sessions LIMIT 1")
    print(f"Session: {session}")
    columns = db.fetchall("PRAGMA table_info(sessions)")
    print("Sessions Columns:")
    for col in columns:
        print(f" - {col['name']}")
    
    columns = db.fetchall("PRAGMA table_info(features)")
    print("Features Columns:")
    for col in columns:
        print(f" - {col['name']}")
except Exception as e:
    print(f"Error: {e}")
