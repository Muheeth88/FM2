from abc import ABC, abstractmethod


class AbstractDriverDetector(ABC):

    def __init__(self, repo_root: str):
        self.repo_root = repo_root

    @abstractmethod
    def detect_driver(self):
        """
        Returns:
        {
            driver_type,
            initialization_pattern,
            thread_model
        }
        """
        pass
