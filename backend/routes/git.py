from fastapi import APIRouter, HTTPException
from models import VerifyRepoRequest, VerifyRepoResponse
from services.git_service import GitService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/git", tags=["git"])

@router.post("/connect", response_model=VerifyRepoResponse)
async def verify_repo_and_fetch_branches(request: VerifyRepoRequest):
    """
    Verifies access to the repository and fetches branches.
    """
    logger.info(f"Verifying repo: {request.repo_url}")
    
    if not GitService.verify_access(request.repo_url, request.pat):
        raise HTTPException(status_code=400, detail="Could not access repository. Check URL and PAT.")
    
    branches = GitService.get_branches(request.repo_url, request.pat)
    if not branches:
        raise HTTPException(status_code=400, detail="Could not fetch branches. Ensure the repository is not empty.")
    
    return VerifyRepoResponse(branches=branches, message="Repository verified successfully")
