from abc import ABC, abstractmethod
from typing import Dict, Set


class AbstractDependencyAnalyzer(ABC):

    def __init__(self, repo_root: str):
        self.repo_root = repo_root
        self.graph = {}  # file_path -> set(dependencies)

    @abstractmethod
    def analyze(self) -> Dict[str, Set[str]]:
        """
        Build dependency graph for entire repo.
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
