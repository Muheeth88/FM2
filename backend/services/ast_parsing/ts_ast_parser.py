import os
from typing import Dict, List

from tree_sitter import Parser
from tree_sitter_languages import get_language

from .base_ast_parser import BaseASTParser


class TypeScriptASTParser(BaseASTParser):

    def __init__(self, repo_root: str):
        super().__init__(repo_root)
        self.language = get_language("typescript")
        self.parser = Parser()
        self.parser.set_language(self.language)

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
            with open(full_path, "rb") as f:
                source_code = f.read()

            tree = self.parser.parse(source_code)
            root = tree.root_node

            self._walk_tree(root, source_code, result)

        except Exception:
            pass

        return result

    def _walk_tree(self, node, source_code: bytes, result: Dict):

        # -----------------------------
        # Import Detection
        # -----------------------------
        if node.type == "import_statement":
            module_node = node.child_by_field_name("source")
            if module_node:
                module_text = source_code[module_node.start_byte:module_node.end_byte].decode("utf-8")
                result["imports"].append(module_text.strip('"').strip("'"))

        # -----------------------------
        # Class Detection
        # -----------------------------
        if node.type == "class_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = source_code[name_node.start_byte:name_node.end_byte].decode("utf-8")
                result["classes"].append(name)

        # -----------------------------
        # Function Detection
        # -----------------------------
        if node.type in ["function_declaration", "method_definition"]:
            name_node = node.child_by_field_name("name")
            if name_node:
                name = source_code[name_node.start_byte:name_node.end_byte].decode("utf-8")
                result["functions"].append(name)

        # -----------------------------
        # Test Detection (Jest / Cypress / Playwright)
        # -----------------------------
        if node.type == "call_expression":
            function_node = node.child_by_field_name("function")
            if function_node:
                fn_name = source_code[function_node.start_byte:function_node.end_byte].decode("utf-8")

                if fn_name in ["test", "it", "describe"]:
                    result["is_test"] = True

                if fn_name in ["beforeEach", "afterEach", "beforeAll", "afterAll"]:
                    result["hooks"].append(fn_name)

        for child in node.children:
            self._walk_tree(child, source_code, result)
