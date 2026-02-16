from pydantic import BaseModel
from typing import Optional, List, Dict

class VerifyRepoRequest(BaseModel):
    repo_url: str
    pat: Optional[str] = None

class VerifyRepoResponse(BaseModel):
    branches: List[str]
    message: str

class CreateSessionRequest(BaseModel):
    name: str
    source_repo_url: str
    target_repo_url: Optional[str] = None
    source_framework: str
    target_framework: str
    base_branch: str
    pat: Optional[str] = None

class CreateSessionResponse(BaseModel):
    session_id: str
    status: str

class TestMethod(BaseModel):
    name: str
    annotations: List[str] = []

class FeatureModel(BaseModel):
    feature_name: str
    file_path: str
    tests: List[TestMethod]
    lifecycle_hooks: List[str]
    framework: str
    language: str

class JavaFileDependency(BaseModel):
    package: Optional[str]
    imports: List[str]
    class_name: Optional[str]
    type: str

class BuildDependency(BaseModel):
    name: Optional[str]
    version: Optional[str]
    type: Optional[str]

class DriverModel(BaseModel):
    driver_type: Optional[str]
    initialization_pattern: Optional[str]
    thread_model: Optional[str]

class AssertionModel(BaseModel):
    file_path: str
    assertion_type: str
    library: str

class ConfigFileModel(BaseModel):
    file_path: str
    type: str

class AnalysisResponse(BaseModel):
    session_id: str
    repo_root: str
    language: str
    framework: str
    build_system: str
    dependency_graph: Dict[str, JavaFileDependency]
    features: List[FeatureModel]
    build_dependencies: List[BuildDependency]
    driver_model: Optional[DriverModel]
    assertions: List[AssertionModel]
    config_files: List[ConfigFileModel]
    shared_modules: List[str] = []
