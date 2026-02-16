import os
from pathlib import Path
from tree_sitter import Language, Parser
import tree_sitter_typescript as ts_ts
from .base_analyzer import AbstractDependencyAnalyzer


class TSDependencyAnalyzer(AbstractDependencyAnalyzer):

    def __init__(self, repo_root):
        super().__init__(repo_root)
        self.parser = Parser(Language(ts_ts.language_typescript()))
        self._index_repo(".ts")

    def analyze(self):
        for file_path in self.all_files:
            if file_path.endswith((".ts", ".js", ".tsx", ".jsx")):
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
            tree = self.parser.parse(bytes(code, "utf-8"))

            file_type = "test" if any(x in file_path.lower() for x in [".test.", ".spec.", "tests/"]) else "source"
            self.metadata[file_path] = {"type": file_type}

            deps = set()
            
            # recursive traversal for tree-sitter
            stack = [tree.root_node]
            while stack:
                node = stack.pop()
                
                # 1. Standard imports
                if node.type == "import_statement":
                    text = code[node.start_byte:node.end_byte]
                    if "from" in text:
                        try:
                            module = text.split("from")[1].strip().strip(";").strip().strip('"').strip("'")
                            resolved = self.resolve_import(file_path, module)
                            if resolved: deps.add(resolved)
                        except: pass
                
                # 2. Config string literals
                elif node.type == "string":
                    # Get value without quotes
                    val = code[node.start_byte:node.end_byte].strip('"').strip("'").strip("`")
                    if val in self.config_map:
                        deps.add(self.config_map[val])
                
                for child in node.children:
                    stack.append(child)

            self.graph[file_path] = deps
        except:
            self.graph[file_path] = set()
            self.metadata[file_path] = {"type": "unknown"}

    def resolve_import(self, from_file, import_path):
        if not import_path.startswith("."):
            return None

        # Absolute paths (if already resolved)
        if os.path.isabs(import_path):
            return import_path.replace("\\", "/")

        base = Path(from_file).parent
        full = (base / import_path).resolve()

        for ext in [".ts", ".js", ".tsx", ".jsx", "/index.ts", "/index.js"]:
            candidate = Path(str(full) + ext)
            if candidate.exists():
                return str(candidate).replace("\\", "/")

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

