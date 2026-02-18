import os


class RepoDiscovery:

    @staticmethod
    def detect_language(repo_root):
        counts = {"java": 0, "typescript": 0, "python": 0}
        skip_dirs = {".git", "node_modules", "venv", "target", "build", "dist", "bin", "obj"}

        for root, dirs, files in os.walk(repo_root):
            # Prune directories to skip in-place
            dirs[:] = [d for d in dirs if d not in skip_dirs]

            for file in files:
                if file.endswith(".java"):
                    counts["java"] += 1
                elif file.endswith((".ts", ".js", ".tsx", ".jsx")):
                    counts["typescript"] += 1
                elif file.endswith(".py"):
                    counts["python"] += 1

        if not any(counts.values()):
            return "unknown"

        # Return the language with the maximum file count
        return max(counts, key=counts.get)

    @staticmethod
    def detect_build_system(repo_root):
        if os.path.exists(f"{repo_root}/pom.xml"):
            return "maven"
        if os.path.exists(f"{repo_root}/package.json"):
            return "npm"
        if os.path.exists(f"{repo_root}/requirements.txt"):
            return "pip"
        return "unknown"
