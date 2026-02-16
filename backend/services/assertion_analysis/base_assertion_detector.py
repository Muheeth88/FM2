from abc import ABC, abstractmethod
from typing import List, Dict


class AbstractAssertionDetector(ABC):

    def __init__(self, repo_root: str):
        self.repo_root = repo_root

    @abstractmethod
    def detect_assertions(self) -> List[Dict]:
        """
        Returns list of:
        {
            file_path,
            assertion_type,
            library
        }
        """
        pass
