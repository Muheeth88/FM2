import os
import ast
from pathlib import Path
from .base_analyzer import AbstractDependencyAnalyzer


class PythonDependencyAnalyzer(AbstractDependencyAnalyzer):

    def __init__(self, repo_root):
        super().__init__(repo_root)
        self.metadata = {}

    def analyze(self):
        for root, _, files in os.walk(self.repo_root):
            for file in files:
                if file.endswith(".py"):
                    file_path = str(Path(root) / file)
                    self.parse_file(file_path)

        result = {}
        for file_path, imports in self.graph.items():
            meta = self.metadata.get(file_path, {})
            result[file_path] = {
                "imports": list(imports),
                "package": None,
                "type": meta.get("type", "source")
            }
        return result

    def parse_file(self, file_path):
        try:
            code = Path(file_path).read_text(encoding="utf-8")
            tree = ast.parse(code)
            
            file_type = "test" if "test" in file_path.lower() else "source"
            self.metadata[file_path] = {"type": file_type}

            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)

            self.graph[file_path] = imports
        except:
            self.graph[file_path] = set()
            self.metadata[file_path] = {"type": "unknown"}

    def build_dependency_tree(self, entry_file):
        visited = set()
        stack = [entry_file]

        while stack:
            current = stack.pop()
            if current in visited:
                continue

            visited.add(current)
            stack.extend(self.graph.get(current, []))

        return visited
