from .java_dependency_analyzer import JavaDependencyAnalyzer
from .ts_and_js_dependency_analyzer import TSDependencyAnalyzer
from .python_dependency_analyzer import PythonDependencyAnalyzer


class DependencyAnalyzerFactory:

    @staticmethod
    def get_analyzer(language: str, repo_root: str):

        if language.lower() == "java":
            return JavaDependencyAnalyzer(repo_root)

        if language.lower() in ["ts", "typescript", "js", "javascript"]:
            return TSDependencyAnalyzer(repo_root)

        if language.lower() == "python":
            return PythonDependencyAnalyzer(repo_root)

        raise ValueError("Unsupported language")
