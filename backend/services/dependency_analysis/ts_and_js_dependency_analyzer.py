import os
from pathlib import Path
from tree_sitter import Language, Parser
import tree_sitter_typescript as ts_ts
from .base_analyzer import AbstractDependencyAnalyzer


class TSDependencyAnalyzer(AbstractDependencyAnalyzer):

    def __init__(self, repo_root):
        super().__init__(repo_root)
        self.parser = Parser(Language(ts_ts.language_typescript()))
        self.metadata = {}

    def analyze(self):
        for root, _, files in os.walk(self.repo_root):
            for file in files:
                if file.endswith((".ts", ".js")):
                    file_path = str(Path(root) / file)
                    self.parse_file(file_path)

        result = {}
        for file_path, imports in self.graph.items():
            meta = self.metadata.get(file_path, {})
            result[file_path] = {
                "imports": list(imports),
                "package": None, # TS doesn't have Java-style packages normally
                "type": meta.get("type", "source")
            }
        return result

    def parse_file(self, file_path):
        code = Path(file_path).read_text(encoding="utf-8")
        tree = self.parser.parse(bytes(code, "utf-8"))

        file_type = "test" if any(x in file_path.lower() for x in [".test.", ".spec.", "tests/"]) else "source"
        self.metadata[file_path] = {"type": file_type}

        imports = set()
        for node in tree.root_node.children:
            if node.type == "import_statement":
                text = code[node.start_byte:node.end_byte]
                if "from" in text:
                    try:
                        module = text.split("from")[1].strip().strip(";").strip().strip('"').strip("'")
                        resolved = self.resolve_import(file_path, module)
                        if resolved:
                            imports.add(resolved)
                    except:
                        continue

        self.graph[file_path] = imports

    def resolve_import(self, from_file, import_path):
        if not import_path.startswith("."):
            return None

        base = Path(from_file).parent
        full = (base / import_path).resolve()

        for ext in [".ts", ".js", "/index.ts", "/index.js"]:
            candidate = Path(str(full) + ext)
            if candidate.exists():
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
            stack.extend(self.graph.get(current, []))

        return visited
