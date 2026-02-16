from .java_assertion_detector import JavaAssertionDetector
from .ts_assertion_detector import TSAssertionDetector
from .python_assertion_detector import PythonAssertionDetector


class AssertionDetectorFactory:

    @staticmethod
    def get_detector(language, repo_root):

        if language == "java":
            return JavaAssertionDetector(repo_root)

        if language in ["typescript", "js", "javascript"]:
            return TSAssertionDetector(repo_root)

        if language == "python":
            return PythonAssertionDetector(repo_root)

        raise ValueError("Unsupported language")
