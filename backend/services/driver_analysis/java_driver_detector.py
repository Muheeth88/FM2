import os
from pathlib import Path
from .base_driver_detector import AbstractDriverDetector


class JavaDriverDetector(AbstractDriverDetector):

    def detect_driver(self):
        driver_type = "WebDriver"
        pattern = "unknown"
        thread_model = "unknown"

        for root, _, files in os.walk(self.repo_root):
            for file in files:
                if file.endswith(".java"):
                    try:
                        content = Path(root, file).read_text(errors='ignore')

                        if "new ChromeDriver" in content or "new FirefoxDriver" in content:
                            if pattern == "unknown":
                                pattern = "inline"

                        if "ThreadLocal<WebDriver>" in content or "ThreadLocal<RemoteWebDriver>" in content:
                            thread_model = "ThreadLocal"

                        if "extends Base" in content or "extends BaseTest" in content:
                            pattern = "Base Class Inheritance"
                            
                        if "getDriver()" in content:
                            pattern = "Driver Factory / Manager"

                    except Exception:
                        continue
                
                if file == "testng.xml":
                    try:
                        content = Path(root, file).read_text(errors='ignore')
                        if 'parallel="' in content:
                            if thread_model == "unknown":
                                thread_model = "TestNG Parallel Execution"
                    except Exception:
                        pass

        return {
            "driver_type": driver_type,
            "initialization_pattern": pattern,
            "thread_model": thread_model
        }
