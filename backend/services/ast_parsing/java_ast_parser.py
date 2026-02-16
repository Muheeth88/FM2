import os
from typing import Dict

from tree_sitter import Parser
from tree_sitter_languages import get_language

from .base_ast_parser import BaseASTParser


class JavaASTParser(BaseASTParser):

    def __init__(self, repo_root: str):
        super().__init__(repo_root)
        self.language = get_language("java")
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
        if node.type == "import_declaration":
            text = source_code[node.start_byte:node.end_byte].decode("utf-8")
            cleaned = text.replace("import", "").replace(";", "").strip()
            result["imports"].append(cleaned)

        # -----------------------------
        # Class Detection
        # -----------------------------
        if node.type == "class_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = source_code[name_node.start_byte:name_node.end_byte].decode("utf-8")
                result["classes"].append(name)

        # -----------------------------
        # Method Detection
        # -----------------------------
        if node.type == "method_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = source_code[name_node.start_byte:name_node.end_byte].decode("utf-8")
                result["functions"].append(name)

        # -----------------------------
        # Annotation Detection
        # -----------------------------
        if node.type == "marker_annotation":
            annotation_text = source_code[node.start_byte:node.end_byte].decode("utf-8")

            if "@Test" in annotation_text:
                result["is_test"] = True

            if annotation_text in [
                "@BeforeSuite",
                "@BeforeMethod",
                "@AfterMethod",
                "@BeforeClass",
                "@AfterClass"
            ]:
                result["hooks"].append(annotation_text)

        for child in node.children:
            self._walk_tree(child, source_code, result)
