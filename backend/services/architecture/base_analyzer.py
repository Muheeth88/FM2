from abc import ABC, abstractmethod
from .architecture_model import ArchitectureModel


class BaseArchitectureAnalyzer(ABC):

    @abstractmethod
    def analyze(self, workspace_path: str) -> ArchitectureModel:
        pass