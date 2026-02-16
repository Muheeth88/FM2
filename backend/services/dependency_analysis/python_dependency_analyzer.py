import os
import ast
from pathlib import Path
from .base_analyzer import AbstractDependencyAnalyzer


class PythonDependencyAnalyzer(AbstractDependencyAnalyzer):

    def __init__(self, repo_root):
        super().__init__(repo_root)
        self._index_repo(".py")

    def analyze(self):
        for file_path in self.all_files:
            if file_path.endswith(".py"):
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

            deps = set()
            for node in ast.walk(tree):
                # 1. Standard imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        resolved = self.resolve_import(file_path, alias.name)
                        if resolved: deps.add(resolved)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        resolved = self.resolve_import(file_path, node.module)
                        if resolved: deps.add(resolved)
                
                # 2. Config string literals
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    val = node.value
                    if val in self.config_map:
                        deps.add(self.config_map[val])
                # Compatibility for older python versions
                elif hasattr(ast, 'Str') and isinstance(node, ast.Str):
                    if node.s in self.config_map:
                        deps.add(self.config_map[node.s])

            self.graph[file_path] = deps
        except:
            self.graph[file_path] = set()
            self.metadata[file_path] = {"type": "unknown"}

    def resolve_import(self, from_file, import_path):
        """Standard Python import resolution (simplified)."""
        # Convert modules to paths: utils.helper -> utils/helper.py
        rel_target = import_path.replace(".", "/") + ".py"
        
        # Check relative (same dir)
        base = os.path.dirname(from_file)
        target = f"{base}/{os.path.basename(rel_target)}"
        if os.path.exists(target):
             return target.replace("\\", "/")

        # Check from repo root
        root_target = f"{self.repo_root}/{rel_target}"
        if os.path.exists(root_target):
            return root_target.replace("\\", "/")

        return None

    def build_dependency_tree(self, entry_file):
        visited = set()
        stack = [entry_file]
        while stack:
            current = stack.pop()
            if current in visited: continue
            visited.add(current)
            stack.extend(self.graph.get(current, []))
        return visited

