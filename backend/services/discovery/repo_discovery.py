import os


class RepoDiscovery:

    @staticmethod
    def detect_language(repo_root):

        for root, _, files in os.walk(repo_root):
            for file in files:
                if file.endswith(".java"):
                    return "java"
                if file.endswith((".ts", ".js")):
                    return "typescript"
                if file.endswith(".py"):
                    return "python"

        return "unknown"

    @staticmethod
    def detect_build_system(repo_root):
        if os.path.exists(f"{repo_root}/pom.xml"):
            return "maven"
        if os.path.exists(f"{repo_root}/package.json"):
            return "npm"
        if os.path.exists(f"{repo_root}/requirements.txt"):
            return "pip"
        return "unknown"
