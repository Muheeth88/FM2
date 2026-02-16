import sqlite3
import os

DB_PATH = "migration_system.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("Running manual migration...")
try:
    cursor.execute("ALTER TABLE sessions ADD COLUMN status TEXT DEFAULT 'PENDING'")
    print("Added status to sessions")
except Exception as e:
    print(f"Sessions migration failed: {e}")

try:
    cursor.execute("ALTER TABLE features ADD COLUMN hooks TEXT")
    print("Added hooks to features")
except Exception as e:
    print(f"Features hooks migration failed: {e}")

try:
    cursor.execute("ALTER TABLE features ADD COLUMN status TEXT DEFAULT 'NOT_MIGRATED'")
    print("Added status to features")
except Exception as e:
    print(f"Features status migration failed: {e}")

try:
    cursor.execute("ALTER TABLE features ADD COLUMN last_migrated_commit TEXT")
    print("Added last_migrated_commit to features")
except Exception as e:
    print(f"Features commit migration failed: {e}")

conn.commit()

cursor.execute("PRAGMA table_info(sessions)")
print("Sessions Columns:", [row[1] for row in cursor.fetchall()])

cursor.execute("PRAGMA table_info(features)")
print("Features Columns:", [row[1] for row in cursor.fetchall()])

conn.close()
