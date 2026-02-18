import os
from pathlib import Path
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language
from .base_extractor import AbstractFeatureExtractor


class TSFeatureExtractor(AbstractFeatureExtractor):

    def __init__(self, repo_root: str):
        super().__init__(repo_root)
        self.parser = Parser()
        self.parser.set_language(get_language("typescript"))

    def extract_features(self):
        features = []

        for root, _, files in os.walk(self.repo_root):
            for file in files:
                if file.endswith((".ts", ".js")):
                    file_path = Path(root) / file
                    feature = self.parse_ts_file(file_path)
                    if feature:
                        features.append(feature)

        return features

    def parse_ts_file(self, file_path: Path):
        code = file_path.read_text(encoding="utf-8")
        tree = self.parser.parse(bytes(code, "utf-8"))

        root = tree.root_node
        tests = []
        framework = "Unknown"

        for node in root.children:
            if node.type == "expression_statement":
                text = code[node.start_byte:node.end_byte]

                if "test(" in text:
                    framework = "Playwright"
                    tests.append({"name": text.strip(), "annotations": []})

                if "it(" in text:
                    framework = "Cypress"
                    tests.append({"name": text.strip(), "annotations": []})

        if tests:
            return self.build_feature_model(
                feature_name=file_path.stem,
                file_path=str(file_path),
                tests=tests,
                hooks=[],
                framework=framework,
                language="TypeScript/JavaScript"
            )

        return None
