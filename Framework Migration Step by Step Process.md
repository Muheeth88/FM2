# Framework Migration Step by Step Process

# PHASE 1 — SESSION INITIALIZATION

---

## STEP 1 — Create Migration Session

### What it does

Creates a logical container for a migration process.

### Why

You need isolation and resumability.

### Responsibility

- Insert session row in SQLite
- Validate inputs

### Input

- source_repo_url
- target_repo_url
- source_framework
- target_framework
- base_branch (default: main)

### Processing

- Validate repo URL format
- Ensure source != target
- Generate session_id (UUID)
- Insert into `sessions` table

### Output

```
session_idstatus= CREATED
```

### DB Write

sessions table

---

## STEP 2 — Initialize Workspace

### What it does

Creates folder structure.

### Why

All operations must happen in isolated workspace.

### Responsibility

- Create:
    
    ```
    /workspace/{session_id}/source
    /workspace/{session_id}/target
    ```
    

### Input

session_id

### Processing

- mkdir
- validate permissions

### Output

workspace paths

---

## STEP 3 — Clone Source Repository

### What it does

Clones source repo into workspace.

### Why

You need to analyze source code.

### Responsibility

- Clone repo
- Capture commit hash

### Input

- source_repo_url
- optional PAT

### Processing

```
gitclone source_repo_url ./source
git rev-parse HEAD
```

### Output

```
source_commit_hash
```

### DB Write

Update sessions.source_commit

---

## STEP 4 — Clone Target Repository

### What it does

Clones target repo.

### Why

All generated changes must apply to a real git tree.

### Responsibility

- Clone
- Checkout base branch

### Input

- target_repo_url
- base_branch

### Processing

```
gitclone target_repo_url ./target
git checkout main
git pull
```

If repo doesn’t exist:

- Initialize new git repo

### Output

Target repo ready at base branch.

---

# PHASE 2 — FEATURE DISCOVERY

---

## STEP 5 — Feature Extraction

### What it does

Discovers logical features from source tests.

### Why

Migration happens at feature granularity.

### Responsibility

- Parse test files
- Group logically

### Input

source repo path

### Processing

- Scan for test files
- Parse file names / annotations
- Group into features

### Output

```
[
  {feature_id,name, test_files[]}
]
```

### DB Write

Insert into `features`

status = NOT_MIGRATED

---

## STEP 6 — Detect Previous Migration State

### What it does

Determines if this is partial migration.

### Why

Avoid overwriting migrated features.

### Responsibility

Compare:

- SQLite feature table
- Target repo file tree

### Input

- session_id
- target repo path

### Processing

For each feature:

- Check if test file exists in target
- Compare last_migrated_commit
- Compare source_commit

### Output

Feature status updated to:

- MIGRATED
- NEEDS_UPDATE
- CONFLICTED
- NOT_MIGRATED

### DB Write

Update features.status

---

# PHASE 3 — USER SELECTION

---

## STEP 7 — Select Features for Migration

### What it does

Marks which features to migrate.

### Why

User-controlled scope.

### Responsibility

Update feature rows.

### Input

selected feature_ids

### Processing

Update status → SELECTED

### Output

List of selected features.

---

# PHASE 4 — CREATE MIGRATION RUN

---

## STEP 8 — Create Migration Branch

### What it does

Creates isolated branch for this run.

### Why

Never modify main directly.

### Responsibility

Git branch creation.

### Input

- session_id
- base_branch

### Processing

```
git checkout main
git pull
git checkout -b migration/session_{id}/run_{timestamp}
```

### Output

branch_name

### DB Write

Insert into migration_runs

---

# PHASE 5 — INTENT MODELING

---

## STEP 9 — Intent Extraction

### What it does

Builds canonical semantic model.

### Why

You migrate intent, not syntax.

### Responsibility

Parse AST → Extract:

- actions
- assertions
- flows
- dependencies

### Input

feature.test_files

### Processing

AST traversal

### Output

IntentGraph (JSON)

### DB Write

Insert into feature_intent

---

# PHASE 6 — CODE GENERATION

---

## STEP 10 — Architecture Reconstruction

### What it does

Extracts lifecycle:

- hooks
- setup
- teardown

### Why

Playwright structure must reflect source behavior.

### Input

source repo

### Output

ArchitectureModel

Stored in SQLite.

---

## STEP 11 — Code Generation

### What it does

Writes new code into target repo.

### Why

Actual migration step.

### Responsibility

- Generate page objects
- Generate test files
- Update configs

### Input

- IntentGraph
- ArchitectureModel
- target repo path

### Processing

Write files inside:

```
/workspace/session_id/target
```

Overwrite only selected features.

### Output

Modified file tree.

---

# PHASE 7 — VALIDATION

---

## STEP 12 — Static Validation

### What it does

Ensures code compiles logically.

### Why

Prevent broken PRs.

### Input

target repo

### Processing

- Validate imports
- Detect duplicates
- Type structure validation

### Output

Validation report

### DB Write

validation_reports

---

## STEP 13 — Behavioral Validation

### What it does

Ensures no semantic loss.

### Why

Guarantee feature parity.

### Input

IntentGraph

Generated AST

### Processing

Compare:

- step count
- assertions
- flows

### Output

Consistency result.

---

# PHASE 8 — COMMIT

---

## STEP 14 — Commit Changes

### What it does

Creates commit in migration branch.

### Input

target repo

### Processing

```
gitadd .
gitcommit-m "Migrated features: Login"
```

### Output

commit_hash

### DB Write

migration_runs.commit_hash

---

# PHASE 9 — DIFF GENERATION

---

## STEP 15 — Compute Diff

### What it does

Computes diff between base branch and migration branch.

### Why

User transparency before PR.

### Input

base_branch

migration_branch

### Processing

```
git diff main...migration_branch--unified=3
git diff--name-status
```

Parse:

- file list
- additions
- deletions
- diff text

### Output

Structured diff.

### DB Write

diffs table

---

# PHASE 10 — PR CREATION

---

## STEP 16 — Push Branch

### Input

migration_branch

### Processing

```
gitpush origin migration_branch
```

---

## STEP 17 — Raise PR

### Input

branch_name

### Processing

Call GitHub API.

### Output

PR URL

### DB Write

pull_requests table

---

# PHASE 11 — CLEANUP

---

## STEP 18 — Cleanup Workspace

### Why

Avoid disk growth.

### Input

session_id

### Processing

Delete workspace folder.

Diff remains in SQLite.

---

# 🔁 RESUME FLOW

When session restarts:

1. Check migration_runs table
2. Identify last completed step
3. Continue from next step
4. Re-clone repos if workspace cleaned

---

# 🧨 FAILURE HANDLING

If failure at:

- Intent step → mark feature FAILED
- Validation step → mark PARTIAL
- Commit step → abort run
- PR step → keep branch local

Nothing touches main branch.

---

# 🎯 Final Outcome

System guarantees:

- Safe git workflow
- Deterministic migration
- Feature-level tracking
- Partial migration support
- Diff before PR
- Conflict detection
- Resume support
- Clean workspace lifecycle