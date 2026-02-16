from abc import ABC, abstractmethod
from typing import List, Dict


class AbstractFeatureExtractor(ABC):

    def __init__(self, repo_root: str):
        self.repo_root = repo_root

    @abstractmethod
    def extract_features(self) -> List[Dict]:
        """
        Must return standardized FeatureModel list.
        """
        pass

    def build_feature_model(
        self,
        feature_name: str,
        file_path: str,
        tests: list,
        hooks: list,
        framework: str,
        language: str
    ) -> Dict:
        return {
            "feature_name": feature_name,
            "file_path": file_path,
            "tests": tests,
            "lifecycle_hooks": hooks,
            "framework": framework,
            "language": language
        }
