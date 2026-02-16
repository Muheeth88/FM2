from .java_driver_detector import JavaDriverDetector
from .ts_driver_detector import TSDriverDetector
from .python_driver_detector import PythonDriverDetector


class DriverDetectorFactory:

    @staticmethod
    def get_detector(language, repo_root):

        if language == "java":
            return JavaDriverDetector(repo_root)

        if language in ["typescript", "js", "javascript"]:
            return TSDriverDetector(repo_root)

        if language == "python":
            return PythonDriverDetector(repo_root)

        raise ValueError("Unsupported language")
