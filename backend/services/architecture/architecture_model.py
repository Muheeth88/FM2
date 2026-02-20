from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ArchitectureModel:
    language: str
    framework: str

    driver_model: Optional[str] = None          # singleton | per_test | thread_local
    driver_scope: Optional[str] = None          # suite | class | test | thread

    base_test_class: Optional[str] = None
    inheritance_tree: dict = field(default_factory=dict)

    # Execution Model (Normalized v1.3.0)
    execution: Optional[dict] = None
    data_driven: Optional[bool] = None

    has_global_setup: Optional[bool] = None
    has_per_test_setup: Optional[bool] = None
    has_teardown: Optional[bool] = None

    config_files: List[str] = field(default_factory=list)

    structure_type: Optional[str] = None        # POM | BDD | flat

    # Refined Step 10 fields (v1.2.0)
    driver_init_location: Optional[dict] = None
    driver_teardown_location: Optional[dict] = None
    driver_lifecycle_binding: Optional[dict] = None
    
    parallel_config: Optional[dict] = None
    
    data_provider: Optional[dict] = None
    test_types_detected: List[str] = field(default_factory=list)
    framework_version: Optional[dict] = None
    
    page_object_pattern: Optional[dict] = None
    
    ui_architecture: dict = field(default_factory=dict)
    api_architecture: dict = field(default_factory=dict)
    
    analysis_version: str = "1.3.0"