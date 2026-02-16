import os
from pathlib import Path
from .base_assertion_detector import AbstractAssertionDetector


class PythonAssertionDetector(AbstractAssertionDetector):

    def detect_assertions(self):
        results = []

        for root, _, files in os.walk(self.repo_root):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    file_path = Path(root) / file
                    try:
                        content = file_path.read_text(errors='ignore')

                        if "assert " in content:
                            results.append({
                                "file_path": str(file_path),
                                "assertion_type": "assert",
                                "library": "Built-in/Pytest"
                            })

                        if "self.assert" in content:
                            results.append({
                                "file_path": str(file_path),
                                "assertion_type": "unittest_assert",
                                "library": "Unittest"
                            })
                    except Exception:
                        continue

        return results
