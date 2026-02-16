import os
from pathlib import Path
from .base_driver_detector import AbstractDriverDetector


class PythonDriverDetector(AbstractDriverDetector):

    def detect_driver(self):

        driver_type = "WebDriver"
        pattern = "unknown"

        for root, _, files in os.walk(self.repo_root):
            for file in files:
                if file.endswith(".py"):
                    content = Path(root, file).read_text()

                    if "webdriver.Chrome" in content:
                        pattern = "inline"

        return {
            "driver_type": driver_type,
            "initialization_pattern": pattern,
            "thread_model": "unknown"
        }
