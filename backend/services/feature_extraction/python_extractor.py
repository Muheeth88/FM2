import os
import ast
from pathlib import Path
from .base_extractor import AbstractFeatureExtractor


class PythonFeatureExtractor(AbstractFeatureExtractor):

    def extract_features(self):
        features = []

        for root, _, files in os.walk(self.repo_root):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    feature = self.parse_python_file(file_path)
                    if feature:
                        features.append(feature)

        return features

    def parse_python_file(self, file_path: Path):
        try:
            code = file_path.read_text()
            tree = ast.parse(code)
        except:
            return None

        tests = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("test_"):
                    tests.append({
                        "name": node.name,
                        "annotations": []
                    })

        if tests:
            return self.build_feature_model(
                feature_name=file_path.stem,
                file_path=str(file_path),
                tests=tests,
                hooks=[],
                framework="PyTest",
                language="Python"
            )

        return None
