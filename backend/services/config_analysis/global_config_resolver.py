import os
import re
from typing import Dict, List, Set


class GlobalConfigResolver:
    """
    Resolves global configuration files and maps them to affected features.

    Responsibilities:
    - Detect global test runner configs
    - Detect global setup/teardown files
    - Map configs to features using dependency graph closure
    """

    # -----------------------------------------
    # Known global config filenames
    # -----------------------------------------
    GLOBAL_CONFIG_PATTERNS = [
        r"pytest\.ini",
        r"conftest\.py",
        r"jest\.config\.(js|ts)",
        r"playwright\.config\.(js|ts)",
        r"cypress\.config\.(js|ts)",
        r"testng\.xml",
        r"pom\.xml",
        r"build\.gradle",
        r"package\.json"
    ]

    # -----------------------------------------
    # Setup/Teardown keywords inside config
    # -----------------------------------------
    GLOBAL_HOOK_PATTERNS = [
        r"globalSetup",
        r"globalTeardown",
        r"beforeAll",
        r"afterAll",
        r"@BeforeSuite",
        r"@AfterSuite"
    ]

    def __init__(
        self,
        repo_root: str,
        dependency_graph: Dict[str, Set[str]],
        feature_files: Dict[str, List[str]]
    ):
        """
        :param repo_root: root path of repo
        :param dependency_graph: directed graph {file: {deps}}
        :param feature_files: {feature_id: [test_files]}
        """
        self.repo_root = repo_root
        self.graph = dependency_graph
        self.feature_files = feature_files

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def resolve(self) -> Dict[str, Dict]:
        """
        Returns:
        {
            "global_configs": [...],
            "feature_config_map": {
                feature_id: [config_files]
            }
        }
        """

        global_configs = self._detect_global_configs()

        feature_config_map = self._map_configs_to_features(global_configs)

        return {
            "global_configs": global_configs,
            "feature_config_map": feature_config_map
        }

    # ==========================================================
    # STEP 1 — Detect Global Config Files
    # ==========================================================

    def _detect_global_configs(self) -> List[str]:
        detected = []

        for root, _, files in os.walk(self.repo_root):
            for file in files:
                full_path = os.path.join(root, file)

                relative_path = os.path.relpath(full_path, self.repo_root)

                if self._is_global_config(file):
                    detected.append(relative_path)
                    continue

                if self._contains_global_hook(full_path):
                    detected.append(relative_path)

        return list(set(detected))

    def _is_global_config(self, filename: str) -> bool:
        for pattern in self.GLOBAL_CONFIG_PATTERNS:
            if re.fullmatch(pattern, filename):
                return True
        return False

    def _contains_global_hook(self, file_path: str) -> bool:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            for pattern in self.GLOBAL_HOOK_PATTERNS:
                if re.search(pattern, content):
                    return True

        except Exception:
            pass

        return False

    # ==========================================================
    # STEP 2 — Map Configs To Features
    # ==========================================================

    def _map_configs_to_features(self, global_configs: List[str]) -> Dict[str, List[str]]:

        feature_map = {}

        for feature_id, test_files in self.feature_files.items():

            related_configs = set()

            closure = self._resolve_feature_closure(test_files)

            for config in global_configs:
                if config in closure:
                    related_configs.add(config)

            # If config is global and not referenced directly,
            # assume it affects all features
            for config in global_configs:
                if self._is_global_config(os.path.basename(config)):
                    related_configs.add(config)

            feature_map[feature_id] = list(related_configs)

        return feature_map

    # ==========================================================
    # Recursive Dependency Closure
    # ==========================================================

    def _resolve_feature_closure(self, start_files: List[str]) -> Set[str]:

        visited = set()
        stack = list(start_files)

        while stack:
            current = stack.pop()

            if current in visited:
                continue

            visited.add(current)

            for dep in self.graph.get(current, []):
                if dep not in visited:
                    stack.append(dep)

        return visited
