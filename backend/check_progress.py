from database.db import Database
session_id = "36ac18a9-6559-4e76-8b6f-de557fd9c780"
db = Database()

session = db.fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))
print(f"Session Status: {session['status'] if session else 'Not Found'}")

feature_count = db.fetchone("SELECT COUNT(*) as cnt FROM features WHERE session_id = ?", (session_id,))
print(f"Features found: {feature_count['cnt']}")

dep_count = db.fetchone("SELECT COUNT(*) as cnt FROM dependency_edges WHERE session_id = ?", (session_id,))
print(f"Dependencies found: {dep_count['cnt']}")

configs = db.fetchone("SELECT COUNT(*) as cnt FROM config_files WHERE session_id = ?", (session_id,))
print(f"Configs found: {configs['cnt']}")

shared = db.fetchone("SELECT COUNT(*) as cnt FROM shared_modules WHERE session_id = ?", (session_id,))
print(f"Shared modules found: {shared['cnt']}")

feature_deps = db.fetchone("SELECT COUNT(*) as cnt FROM feature_dependencies WHERE session_id = ?", (session_id,))
print(f"Feature closures built: {feature_deps['cnt']}")
