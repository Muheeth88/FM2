import os
import re


class ExecutionAnalyzer:

    def analyze(self, workspace_path):
        parallel_config = {"enabled": None, "type": None, "thread_count": None}
        parallel_capable = None
        data_driven = None
        data_provider = {"type": None, "scope": None}
        config_files = []

        for root, dirs, files in os.walk(workspace_path):
            for f in files:
                f_path = os.path.join(root, f)
                
                # Broad config file detection
                if f.endswith((".xml", ".properties", ".yaml", ".yml", ".json", ".conf")):
                    if any(term in f.lower() for term in ["config", "env", "test", "prop", "pom"]):
                        config_files.append(f)

                if f == "testng.xml":
                    with open(f_path, "r", encoding="utf-8") as file:
                        content = file.read()
                        if 'parallel="' in content:
                            parallel_config["enabled"] = True
                            parallel_capable = True
                            p_match = re.search(r'parallel="([^"]+)"', content)
                            if p_match: parallel_config["type"] = p_match.group(1)
                            t_match = re.search(r'thread-count="([^"]+)"', content)
                            if t_match: parallel_config["thread_count"] = int(t_match.group(1))

                if f == "pom.xml":
                    with open(f_path, "r", encoding="utf-8") as file:
                        content = file.read()
                        if "<parallel>" in content:
                            parallel_config["enabled"] = True
                            parallel_capable = True
                            p_match = re.search(r"<parallel>([^<]+)</parallel>", content)
                            if p_match: parallel_config["type"] = p_match.group(1).strip()
                        if "<threadCount>" in content:
                            t_match = re.search(r"<threadCount>([^<]+)</threadCount>", content)
                            if t_match: parallel_config["thread_count"] = int(t_match.group(1))

                if f.endswith(".java"):
                    with open(f_path, "r", encoding="utf-8") as file:
                        content = file.read()
                        if "ThreadLocal<WebDriver>" in content:
                            parallel_capable = True
                        if "@DataProvider" in content:
                            data_driven = True
                            data_provider["type"] = "TestNG"
                            data_provider["scope"] = "method"
                        elif "@ParameterizedTest" in content:
                            data_driven = True
                            data_provider["type"] = "JUnit5"
                            data_provider["scope"] = "method"

        # Determine mode
        mode = None
        if parallel_config["enabled"] is True:
            mode = "parallel"
        elif parallel_config["enabled"] is False:
            mode = "serial"
        # If still None, it stays None (unknown)

        return {
            "mode": mode,
            "parallel_config": parallel_config,
            "parallel_capable": parallel_capable,
            "data_driven": data_driven,
            "data_provider": data_provider,
            "config_files": list(set(config_files))
        }
