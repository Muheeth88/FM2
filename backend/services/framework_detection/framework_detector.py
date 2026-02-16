import os


class FrameworkDetector:

    @staticmethod
    def detect(repo_root, language):

        if language == "java":
            return FrameworkDetector._detect_java(repo_root)

        if language == "typescript":
            return FrameworkDetector._detect_ts(repo_root)

        if language == "python":
            return FrameworkDetector._detect_python(repo_root)

        return "unknown"

    @staticmethod
    def _detect_java(repo_root):
        for root, _, files in os.walk(repo_root):
            for file in files:
                if file.endswith(".java"):
                    content = open(os.path.join(root, file)).read()
                    if "org.junit" in content:
                        return "JUnit"
                    if "org.testng" in content:
                        return "TestNG"
        return "unknown"

    @staticmethod
    def _detect_ts(repo_root):
        package_json = f"{repo_root}/package.json"
        if os.path.exists(package_json):
            content = open(package_json).read()
            if "cypress" in content:
                return "Cypress"
            if "@playwright/test" in content:
                return "Playwright"
        return "unknown"

    @staticmethod
    def _detect_python(repo_root):
        for root, _, files in os.walk(repo_root):
            for file in files:
                if file.endswith(".py"):
                    content = open(os.path.join(root, file)).read()
                    if "pytest" in content:
                        return "PyTest"
        return "unknown"
