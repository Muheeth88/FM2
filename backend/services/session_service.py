import uuid
import logging
from models import (
    CreateSessionRequest, 
    CreateSessionResponse, 
    SelectFeaturesRequest, 
    CreateRunRequest, 
    MigrationRunResponse
)
from database import get_db_connection
from services.workspace_service import WorkspaceService
from services.git_service import GitService

logger = logging.getLogger(__name__)

class SessionService:
    @staticmethod
    def create_session(request: CreateSessionRequest) -> CreateSessionResponse:
        # Validate inputs
        if not request.source_repo_url:
            raise ValueError("Source repository URL is required.")
        if not request.source_framework or not request.target_framework:
            raise ValueError("Source and target frameworks are required.")

        session_id = str(uuid.uuid4())
        status = "CREATED"
        logger.info(f"Full CreateSessionRequest: {request.dict()}")
        
        try:
            logger.info(f"Creating session with target_url: {request.target_repo_url}, base_branch: {request.base_branch}")
            logger.info("Executing STEP 1: Workspace Init")
            # STEP 1: Initialize Workspace
            ws = WorkspaceService.initialize_workspace(session_id)
            source_path = ws["source_path"]
            target_path = ws["target_path"]

            logger.info("Executing STEP 2: Clone Source")
            # STEP 2: Clone Source Repository
            if not GitService.clone_repo(request.source_repo_url, source_path, request.pat, request.base_branch):
                logger.info("Clone with branch failed, trying default...")
                if not GitService.clone_repo(request.source_repo_url, source_path, request.pat):
                    raise RuntimeError("Failed to clone source repository.")
            
            logger.info("Executing STEP 3: DB Insert")
            # STEP 3: Insert session row in SQLite
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sessions (
                    id, repo_root, language, framework, build_system,
                    source_repo_url, target_repo_url, target_repo_mode,
                    target_repo_name, target_repo_owner, base_branch, status
                ) VALUES (
                    :id, :repo_root, :language, :framework, :build_system,
                    :source_repo_url, :target_repo_url, :target_repo_mode,
                    :target_repo_name, :target_repo_owner, :base_branch, :status
                )
            ''', {
                "id": session_id,
                "repo_root": source_path,
                "language": "unknown",
                "framework": request.source_framework,
                "build_system": "unknown",
                "source_repo_url": request.source_repo_url,
                "target_repo_url": request.target_repo_url,
                "target_repo_mode": request.target_repo_mode,
                "target_repo_name": request.target_repo_name,
                "target_repo_owner": request.target_repo_owner,
                "base_branch": request.base_branch,
                "status": "INITIALIZED"
            })
            
            conn.commit()
            conn.close()
            logger.info(f"Session created and saved to DB with ID: {session_id}")

            logger.info("Executing STEP 4: Clone/Init Target")
            # STEP 4: Clone / Initialize Target Repository
            target_cloned = False
            final_target_url = request.target_repo_url

            if request.target_repo_mode == "new":
                if request.target_repo_name and request.target_repo_owner and request.pat:
                    from services.github_service import GitHubService
                    logger.info(f"Creating new target repo: {request.target_repo_owner}/{request.target_repo_name}")
                    final_target_url = GitHubService.create_repository(
                        name=request.target_repo_name,
                        owner=request.target_repo_owner,
                        pat=request.pat,
                        visibility=request.target_repo_visibility or "public"
                    )
                    
                    if not final_target_url:
                        raise RuntimeError(f"Failed to create new repository '{request.target_repo_name}' via GitHub API.")
                        
                    # Update session with the actual target URL
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE sessions SET target_repo_url = :url WHERE id = :id", {"url": final_target_url, "id": session_id})
                    conn.commit()
                    conn.close()
                    logger.info(f"Updated session {session_id} with new target_url: {final_target_url}")
                else:
                    raise ValueError("Missing repository name, owner, or PAT for 'new' repository mode.")

            if final_target_url:
                logger.info(f"Attempting to clone target repo: {final_target_url}")
                target_cloned = GitService.clone_repo(final_target_url, target_path, request.pat)
            
            if not target_cloned:
                if request.target_repo_mode == "existing":
                    logger.warning("Target repo clone failed, falling back to local init.")
                else:
                    logger.info("New repository is empty or clone failed. Initializing locally.")
                GitService.init_repo(target_path)
            
            logger.info("Session initialization complete")
        except Exception as e:
            logger.error(f"Failed to complete session initialization: {str(e)}")
            # Update session status if possible
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE sessions SET status = 'FAILED', error_message = ? WHERE id = ?", (str(e), session_id))
                conn.commit()
                conn.close()
            except:
                pass
            raise RuntimeError(f"Initialization failed: {str(e)}")
        
        return CreateSessionResponse(session_id=session_id, status=status)

    @staticmethod
    def select_features(request: SelectFeaturesRequest) -> bool:
        """
        Marks selected features for migration.
        """
        if not request.feature_ids:
            raise ValueError("At least one feature must be selected.")
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Clear previous selections for this session
            cursor.execute("UPDATE features SET status = 'NOT_MIGRATED' WHERE session_id = ? AND status = 'SELECTED'", (request.session_id,))
            
            # 2. Mark new selections
            placeholders = ','.join(['?'] * len(request.feature_ids))
            query = f"UPDATE features SET status = 'SELECTED' WHERE session_id = ? AND id IN ({placeholders})"
            cursor.execute(query, [request.session_id] + request.feature_ids)
            
            conn.commit()
            logger.info(f"Selected {len(request.feature_ids)} features for session {request.session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to select features: {str(e)}")
            return False
        finally:
            conn.close()

    @staticmethod
    def create_migration_run(request: CreateRunRequest) -> MigrationRunResponse:
        """
        Starts a migration run by creating a branch and registering it in DB.
        """
        import datetime
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Get session info
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (request.session_id,))
            session_row = cursor.fetchone()
            if not session_row:
                raise ValueError(f"Session {request.session_id} not found.")
            
            session = dict(session_row)
            logger.info(f"Loaded session data for run: {session}")
            
            ws_paths = WorkspaceService.initialize_workspace(request.session_id)
            target_path = ws_paths["target_path"]
            base_branch = session["base_branch"] or "main"
            target_repo_url = session["target_repo_url"]
            
            # 2. Create Branch Name
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            branch_name = f"migration/session_{request.session_id[:8]}/run_{timestamp}"
            
            # 3. Create branch via GitService
            if not GitService.create_branch(target_path, branch_name, base_branch):
                raise RuntimeError(f"Failed to create git branch {branch_name}")
            
            # 4. Push branch to remote (DISABLED for now as per user request)
            # logger.info(f"Pushing branch {branch_name} to remote...")
            # GitService.push_branch(target_path, branch_name)
            
            # 5. Insert Run record
            run_id = str(uuid.uuid4())
            started_at = datetime.datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO migration_runs (id, session_id, branch_name, status, started_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (run_id, request.session_id, branch_name, "RUNNING", started_at))
            
            conn.commit()
            logger.info(f"Migration run created: {run_id} on branch {branch_name}")
            
            return MigrationRunResponse(
                run_id=run_id,
                session_id=request.session_id,
                branch_name=branch_name,
                target_repo_url=target_repo_url or "unknown",
                base_branch=base_branch,
                status="RUNNING",
                started_at=started_at
            )
        except Exception as e:
            logger.error(f"Failed to create migration run: {str(e)}")
            raise RuntimeError(f"Run creation failed: {str(e)}")
        finally:
            conn.close()
