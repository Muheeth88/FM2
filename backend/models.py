from pydantic import BaseModel
from typing import Optional, List

class VerifyRepoRequest(BaseModel):
    repo_url: str
    pat: Optional[str] = None

class VerifyRepoResponse(BaseModel):
    branches: List[str]
    message: str

class CreateSessionRequest(BaseModel):
    source_repo_url: str
    source_framework: str
    target_framework: str
    base_branch: str
    pat: Optional[str] = None

class CreateSessionResponse(BaseModel):
    session_id: str
    status: str
