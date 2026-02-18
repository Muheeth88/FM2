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
        skip_dirs = {".git", "node_modules", "venv", "target", "build", "dist", "bin", "obj"}
        for root, dirs, files in os.walk(repo_root):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if file.endswith(".java"):
                    try:
                        with open(os.path.join(root, file), encoding="utf-8", errors="ignore") as f:
                            content = f.read(16384) # Read first 16KB only for detection
                            if "org.junit" in content:
                                return "JUnit"
                            if "org.testng" in content:
                                return "TestNG"
                    except Exception:
                        continue
        return "unknown"

    @staticmethod
    def _detect_ts(repo_root):
        package_json = os.path.join(repo_root, "package.json")
        if os.path.exists(package_json):
            try:
                with open(package_json, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if "cypress" in content:
                        return "Cypress"
                    if "@playwright/test" in content:
                        return "Playwright"
            except Exception:
                pass
        return "unknown"

    @staticmethod
    def _detect_python(repo_root):
        skip_dirs = {".git", "node_modules", "venv", "target", "build", "dist", "bin", "obj"}
        for root, dirs, files in os.walk(repo_root):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if file.endswith(".py"):
                    try:
                        with open(os.path.join(root, file), encoding="utf-8", errors="ignore") as f:
                            content = f.read(16384)
                            if "pytest" in content:
                                return "PyTest"
                    except Exception:
                        continue
        return "unknown"
