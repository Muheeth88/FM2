import os
from pathlib import Path
import javalang
from .base_analyzer import AbstractDependencyAnalyzer


class JavaDependencyAnalyzer(AbstractDependencyAnalyzer):

    def __init__(self, repo_root: str):
        super().__init__(repo_root)
        self.metadata = {}

    # 1️⃣ Scan Java files
    def scan_java_files(self):
        java_files = []
        for root, _, files in os.walk(self.repo_root):
            for file in files:
                if file.endswith(".java"):
                    java_files.append(Path(root) / file)
        return java_files

    # 2️⃣ Detect if file is test file (consistent with FeatureExtractor)
    def is_test_file(self, tree, file_path: Path):
        for _, node in tree.filter(javalang.tree.MethodDeclaration):
            for annotation in node.annotations:
                if annotation.name == "Test":
                    return True
        if "Test" in file_path.name:
            return True
        return False

    def analyze(self):
        java_files = self.scan_java_files()
        for file in java_files:
            self.parse_file(str(file))

        # Merge graph and metadata
        result = {}
        for file_path, imports in self.graph.items():
            meta = self.metadata.get(file_path, {})
            result[file_path] = {
                "imports": list(imports),
                "package": meta.get("package"),
                "type": meta.get("type", "source")
            }
        return result

    def parse_file(self, file_path):
        try:
            p_file_path = Path(file_path)
            code = p_file_path.read_text(encoding="utf-8")
            tree = javalang.parse.parse(code)
            
            # Extract package
            package_name = tree.package.name if tree.package else None
            
            # Use consistent test detection logic
            file_type = "test" if self.is_test_file(tree, p_file_path) else "source"
            
            self.metadata[file_path] = {
                "package": package_name,
                "type": file_type
            }

            imports = set()
            for imp in tree.imports:
                resolved = self.resolve_import(imp.path)
                if resolved:
                    imports.add(resolved)

            self.graph[file_path] = imports
            
        except Exception:
            self.graph[file_path] = set()
            self.metadata[file_path] = {
                "package": None,
                "type": "unknown"
            }

    def resolve_import(self, import_path):
        # Simplistic resolution: match class name in the repo
        class_name = import_path.split(".")[-1]
        
        # In a real-world scenario, we'd use package structure.
        # Here we look for files named ClassName.java
        for root, _, files in os.walk(self.repo_root):
            if class_name + ".java" in files:
                candidate = Path(root) / (class_name + ".java")
                # Return the absolute path as the identifier in the graph
                return str(candidate)

        return None

    def build_dependency_tree(self, entry_file):
        visited = set()
        stack = [entry_file]

        while stack:
            current = stack.pop()
            if current in visited:
                continue

            visited.add(current)

            for dep in self.graph.get(current, []):
                stack.append(dep)

        return visited
