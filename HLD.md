# HLD

+-------------------------------------------------------------+
|                        Frontend (React)                     |
|-------------------------------------------------------------|
| Dashboard |New Migration | Feature Selection               |
| Progress  | Validation    | Diff Viewer | PRSummary        |
+----------------------------+--------------------------------+
                             |
                             v
+-------------------------------------------------------------+
|                     FastAPI Backend                         |
|-------------------------------------------------------------|
|1.Session Manager                                          |
|2. Workspace Manager                                        |
|3. Git Service                                              |
|4. Workflow Engine (Custom)                                 |
|5. Agent Layer (Custom Classes)                             |
|6. Diff Service                                             |
|7. Validation Engine                                        |
|8. PR Service                                               |
+----------------------------+--------------------------------+
                             |
                             v
+----------------------+-----------------------------+
| SQLiteDatabase     | Workspace (Ephemeral)       |
|----------------------|-----------------------------|
| sessions             | /workspace/session_id      |
| features             |   source/                  |
| migration_runs       |   target/                  |
| feature_intent       |                           |
| validation_reports   |                           |
| diffs                |                           |
| pull_requests        |                           |
+----------------------+-----------------------------+
                             |
                             v
                       GitHub / Git Provider
```

---

# 📦 SQLite Schema Overview

### sessions

- id
- source_repo
- target_repo
- source_commit
- target_base_branch
- status

---

### features

- id
- session_id
- name
- status
- last_migrated_commit
- validation_status

---

### migration_runs

- id
- session_id
- branch_name
- status
- started_at
- finished_at

---

### diffs

- id
- run_id
- file_path
- change_type
- additions
- deletions
- diff_text

---

### pull_requests

- id
- run_id
- branch_name
- pr_url
- status