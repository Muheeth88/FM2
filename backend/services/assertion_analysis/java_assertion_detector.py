import os
import javalang
from pathlib import Path
from .base_assertion_detector import AbstractAssertionDetector


class JavaAssertionDetector(AbstractAssertionDetector):

    def detect_assertions(self):
        results = []

        for root, _, files in os.walk(self.repo_root):
            for file in files:
                if file.endswith(".java"):
                    file_path = Path(root) / file
                    try:
                        code = file_path.read_text()
                        tree = javalang.parse.parse(code)
                    except:
                        continue

                    for _, node in tree.filter(javalang.tree.MethodInvocation):
                        name = node.member

                        if name.startswith("assert"):
                            results.append({
                                "file_path": str(file_path),
                                "assertion_type": name,
                                "library": "JUnit/TestNG"
                            })

        return results
