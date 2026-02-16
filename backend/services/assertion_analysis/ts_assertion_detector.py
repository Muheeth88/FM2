import os
from pathlib import Path
from .base_assertion_detector import AbstractAssertionDetector


class TSAssertionDetector(AbstractAssertionDetector):

    def detect_assertions(self):
        results = []

        for root, _, files in os.walk(self.repo_root):
            for file in files:
                if file.endswith((".ts", ".js")):
                    file_path = Path(root) / file
                    content = file_path.read_text()

                    if "expect(" in content:
                        results.append({
                            "file_path": str(file_path),
                            "assertion_type": "expect",
                            "library": "Playwright/Jest"
                        })

                    if ".should(" in content:
                        results.append({
                            "file_path": str(file_path),
                            "assertion_type": "should",
                            "library": "Cypress"
                        })

        return results
