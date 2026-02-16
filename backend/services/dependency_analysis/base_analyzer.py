import os
from abc import ABC, abstractmethod
from typing import Dict, Set, List


class AbstractDependencyAnalyzer(ABC):

    def __init__(self, repo_root: str):
        self.repo_root = repo_root.replace("\\", "/")
        self.graph = {}  # file_path -> set(dependencies)
        self.metadata = {}
        self.config_map = {} # filename -> absolute_path
        self.all_files = [] # List of all absolute paths

    def _index_repo(self, source_ext: str):
        """Common indexing logic for source files and config files."""
        config_exts = [".properties", ".xml", ".json", ".yaml", ".yml", ".env", ".ini", ".toml"]
        for root, _, files in os.walk(self.repo_root):
            for file in files:
                norm_root = root.replace("\\", "/")
                abs_path = f"{norm_root}/{file}"
                self.all_files.append(abs_path)
                
                # Index config files
                for ext in config_exts:
                    if file.endswith(ext):
                        self.config_map[file] = abs_path
                        break

    @abstractmethod
    def analyze(self) -> Dict[str, dict]:
        """
        Build dependency graph for entire repo.
        Returns Dict[file_path, {imports: List, package: str, type: str}]
        """
        pass

    @abstractmethod
    def build_dependency_tree(self, entry_file: str) -> Set[str]:
        """
        Return transitive closure of dependencies.
        """
        pass

    def get_graph(self):
        return self.graph

