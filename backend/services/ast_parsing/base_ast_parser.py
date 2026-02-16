from abc import ABC, abstractmethod
from typing import Dict, List


class BaseASTParser(ABC):

    def __init__(self, repo_root: str):
        self.repo_root = repo_root

    @abstractmethod
    def parse_file(self, file_path: str) -> Dict:
        """
        Returns:
        {
            "imports": [],
            "classes": [],
            "functions": [],
            "hooks": [],
            "is_test": bool
        }
        """
        pass
