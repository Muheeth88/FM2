from .java_extractor import JavaFeatureExtractor
from .ts_extractor import TSFeatureExtractor
from .python_extractor import PythonFeatureExtractor


class FeatureExtractorFactory:

    @staticmethod
    def get_extractor(language: str, repo_root: str):

        if language.lower() == "java":
            return JavaFeatureExtractor(repo_root)

        if language.lower() in ["ts", "typescript", "js", "javascript"]:
            return TSFeatureExtractor(repo_root)

        if language.lower() == "python":
            return PythonFeatureExtractor(repo_root)

        raise ValueError("Unsupported language")
