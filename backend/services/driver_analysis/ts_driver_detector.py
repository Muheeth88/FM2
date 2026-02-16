import os
from pathlib import Path
from .base_driver_detector import AbstractDriverDetector


class TSDriverDetector(AbstractDriverDetector):

    def detect_driver(self):

        driver_type = "browser"
        pattern = "unknown"

        for root, _, files in os.walk(self.repo_root):
            for file in files:
                if file.endswith((".ts", ".js")):
                    content = Path(root, file).read_text()

                    if "browser.newPage" in content:
                        pattern = "factory"

                    if "test.beforeEach" in content:
                        pattern = "hook_based"

        return {
            "driver_type": driver_type,
            "initialization_pattern": pattern,
            "thread_model": "parallel_by_framework"
        }
