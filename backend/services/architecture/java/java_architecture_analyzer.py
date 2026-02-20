import os
from .java_ast_index import JavaASTIndex
from .driver_analyzer import DriverAnalyzer
from .inheritance_analyzer import InheritanceAnalyzer
from .lifecycle_analyzer import LifecycleAnalyzer
from .execution_analyzer import ExecutionAnalyzer
from .scope_analyzer import ScopeAnalyzer
from .structural_analyzer import StructuralAnalyzer
from ..architecture_model import ArchitectureModel


class JavaArchitectureAnalyzer:

    def analyze(self, workspace_path):

        java_files = self._collect_java_files(workspace_path)

        ast_index = JavaASTIndex()
        ast_index.build(java_files)

        model = ArchitectureModel(
            language="java",
            framework="selenium"
        )

        d_analysis = DriverAnalyzer().analyze(ast_index)
        model.driver_model = d_analysis["model"]
        model.driver_scope = d_analysis["scope"]
        model.driver_init_location = d_analysis["init_location"]
        model.driver_teardown_location = d_analysis["teardown_location"]
        model.driver_lifecycle_binding = d_analysis["lifecycle_binding"]

        inh = InheritanceAnalyzer().analyze(ast_index)
        model.inheritance_tree = inh["tree"]
        model.base_test_class = inh["base_test"]

        lifecycle = LifecycleAnalyzer().analyze(ast_index)
        model.has_global_setup = lifecycle["global"]
        model.has_per_test_setup = lifecycle["per_test"]
        model.has_teardown = lifecycle["teardown"]

        exec_model = ExecutionAnalyzer().analyze(workspace_path)
        model.data_driven = exec_model["data_driven"]
        model.parallel_config = exec_model["parallel_config"]
        model.data_provider = exec_model["data_provider"]
        model.config_files = exec_model["config_files"]
        
        # Normalized Execution Model v1.3.0
        model.execution = {
            "configured_mode": exec_model["mode"],
            "parallel_capable": exec_model["parallel_capable"],
            "recommended_playwright_mode": "parallel" if exec_model["parallel_capable"] else "serial"
        }

        struct = StructuralAnalyzer().analyze(ast_index, workspace_path)
        model.structure_type = struct["structure_type"]
        model.test_types_detected = struct["test_types_detected"]
        model.framework_version = struct["framework_version"]
        model.page_object_pattern = struct["page_object_pattern"]
        model.ui_architecture = struct["ui_architecture"]
        model.api_architecture = struct["api_architecture"]

        return model

    def _collect_java_files(self, root):
        files = []
        for r, d, f in os.walk(root):
            for file in f:
                if file.endswith(".java"):
                    files.append(os.path.join(r, file))
        return files