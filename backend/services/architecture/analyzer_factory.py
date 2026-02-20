from .java.java_architecture_analyzer import JavaArchitectureAnalyzer


class ArchitectureAnalyzerFactory:

    @staticmethod
    def get_analyzer(language: str):
        if language.lower() == "java":
            return JavaArchitectureAnalyzer()
        raise NotImplementedError(f"No analyzer for {language}")