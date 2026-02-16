import os
from pathlib import Path
import javalang
from .base_analyzer import AbstractDependencyAnalyzer


class JavaDependencyAnalyzer(AbstractDependencyAnalyzer):

    def __init__(self, repo_root: str):
        super().__init__(repo_root)
        self.java_map = {}   # ClassName -> AbsolutePath (first match, for import resolution)
        self._index_repo(".java")

    def _index_repo(self, source_ext: str):
        """Index Java files for class resolution and config files."""
        super()._index_repo(source_ext)
        for abs_path in self.all_files:
            if abs_path.endswith(".java"):
                class_name = os.path.basename(abs_path).replace(".java", "")
                if class_name not in self.java_map:
                    self.java_map[class_name] = abs_path


    def is_test_file(self, tree, file_path_str: str):
        """Check if a file is a test file using annotations or naming convention."""
        try:
            for _, node in tree.filter(javalang.tree.MethodDeclaration):
                for annotation in node.annotations:
                    if annotation.name == "Test":
                        return True
        except Exception:
            pass
            
        if "Test" in os.path.basename(file_path_str):
            return True
        return False

    def analyze(self):
        """Analyze all Java files to build the dependency graph."""
        # Parse ALL Java files
        for file_path in self.all_files:
            if file_path.endswith(".java"):
                self.parse_file(file_path)

        # Build final result format
        result = {}
        for file_path, deps in self.graph.items():
            meta = self.metadata.get(file_path, {})
            result[file_path] = {
                "imports": list(deps),
                "package": meta.get("package"),
                "type": meta.get("type", "source")
            }
        return result

    def parse_file(self, file_path):
        """Parse a single Java file to extract imports and config references."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            tree = javalang.parse.parse(code)
            
            package_name = tree.package.name if tree.package else None
            file_type = "test" if self.is_test_file(tree, file_path) else "source"
            
            self.metadata[file_path] = {
                "package": package_name,
                "type": file_type
            }

            deps = set()
            
            # 1. Standard imports
            for imp in tree.imports:
                resolved = self.resolve_import(imp.path)
                if resolved:
                    deps.add(resolved)

            # 2. String literal references to config files (e.g. "application.properties")
            try:
                for _, node in tree.filter(javalang.tree.Literal):
                    if isinstance(node.value, str):
                        # Strip quotes and check if it matches any indexed config file
                        val = node.value.strip('"').strip("'")
                        if val in self.config_map:
                            deps.add(self.config_map[val])
            except Exception:
                # AST might fail on some complex literals, ignore and continue
                pass

            self.graph[file_path] = deps
            
        except Exception:
            # If parsing fails for one file, still include it in graph with empty deps
            self.graph[file_path] = set()
            if file_path not in self.metadata:
                self.metadata[file_path] = {
                    "package": None,
                    "type": "unknown"
                }

    def resolve_import(self, import_path):
        """Resolve a package-style import to an absolute file path."""
        class_name = import_path.split(".")[-1]
        return self.java_map.get(class_name)

    def build_dependency_tree(self, entry_file):
        """Transitive closure traversal."""
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
