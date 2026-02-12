from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class MigrationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"

class FeatureStatus(str, Enum):
    NOT_MIGRATED = "NOT_MIGRATED"
    SELECTED = "SELECTED"
    MIGRATING = "MIGRATING"
    MIGRATED = "MIGRATED"
    FAILED = "FAILED"
    PARTIALLY_MIGRATED = "PARTIALLY_MIGRATED"
    NEEDS_UPDATE = "NEEDS_UPDATE"

class ValidationStatus(str, Enum):
    PASSED = "PASSED"
    WARNING = "WARNING"
    ERROR = "ERROR"

class CreateSessionRequest(BaseModel):
    source_repo: str
    target_repo: str
    source_framework: str
    target_framework: str

class MigrationSession(BaseModel):
    session_id: str
    source_repo: str
    target_repo: str
    source_framework: str
    target_framework: str
    status: MigrationStatus
    created_at: datetime
    last_run_at: Optional[datetime] = None

class FeatureEntity(BaseModel):
    feature_id: str
    feature_name: str
    source_files: List[str]
    status: FeatureStatus
    last_migrated_commit: Optional[str] = None
    validation_status: Optional[ValidationStatus] = None
    error_log: Optional[str] = None
