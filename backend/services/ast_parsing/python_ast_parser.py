import ast
import os
from typing import Dict

from .base_ast_parser import BaseASTParser


class PythonASTParser(BaseASTParser):

    def parse_file(self, file_path: str) -> Dict:
        result = {
            "imports": [],
            "classes": [],
            "functions": [],
            "hooks": [],
            "is_test": False
        }

        full_path = os.path.join(self.repo_root, file_path)

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):

                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result["imports"].append(alias.name)

                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        result["imports"].append(node.module)

                if isinstance(node, ast.FunctionDef):
                    result["functions"].append(node.name)

                    if node.name.startswith("test_"):
                        result["is_test"] = True

                if isinstance(node, ast.ClassDef):
                    result["classes"].append(node.name)

        except Exception:
            pass

        return result
