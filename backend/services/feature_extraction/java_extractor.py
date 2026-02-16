import os
from pathlib import Path
import javalang
from .base_extractor import AbstractFeatureExtractor


class JavaFeatureExtractor(AbstractFeatureExtractor):

    def __init__(self, repo_root: str):
        super().__init__(repo_root)
        self.features = []

    # 1️⃣ Scan Java files
    def scan_java_files(self):
        java_files = []
        for root, _, files in os.walk(self.repo_root):
            for file in files:
                if file.endswith(".java"):
                    java_files.append(Path(root) / file)
        return java_files

    # 2️⃣ Detect if file is test file
    def is_test_file(self, tree, file_path: Path):
        # If class has @Test methods
        for _, node in tree.filter(javalang.tree.MethodDeclaration):
            for annotation in node.annotations:
                if annotation.name == "Test":
                    return True

        # Fallback: filename contains Test
        if "Test" in file_path.name:
            return True

        return False

    # 3️⃣ Extract features from file
    def parse_test_file(self, file_path: Path):
        try:
            code = file_path.read_text(encoding="utf-8")
            tree = javalang.parse.parse(code)
        except Exception:
            return

        if not self.is_test_file(tree, file_path):
            return

        for _, class_node in tree.filter(javalang.tree.ClassDeclaration):
            tests = []
            hooks = []

            for method in class_node.methods:
                # Detect test methods
                for annotation in method.annotations:
                    if annotation.name == "Test":
                        tests.append({
                            "name": method.name,
                            "annotations": [a.name for a in method.annotations]
                        })

                # Detect lifecycle hooks
                if any(a.name in ["Before", "BeforeEach", "BeforeMethod"]
                       for a in method.annotations):
                    hooks.append(method.name)

                if any(a.name in ["After", "AfterEach", "AfterMethod"]
                       for a in method.annotations):
                    hooks.append(method.name)

            if tests:
                feature = self.build_feature_model(
                    feature_name=class_node.name,
                    file_path=str(file_path),
                    tests=tests,
                    hooks=hooks,
                    framework="JUnit/TestNG",
                    language="Java"
                )
                self.features.append(feature)

    # 4️⃣ Run extraction
    def extract_features(self):
        self.features = []
        java_files = self.scan_java_files()

        for file in java_files:
            self.parse_test_file(file)

        return self.features
