import os

class ConfigAnalyzer:

    def analyze(self, workspace_path):

        config_files = []

        for root, dirs, files in os.walk(workspace_path):
            for f in files:
                if f.endswith((".properties", ".xml", ".yml", ".yaml")):
                    config_files.append(os.path.join(root, f))

        return {"files": config_files}