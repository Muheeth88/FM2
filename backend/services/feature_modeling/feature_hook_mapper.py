from typing import Dict, List


class FeatureHookMapper:

    def __init__(self, ast_parser):
        self.parser = ast_parser

    def collect_feature_hooks(self, file_paths: List[str]):

        hooks = []

        for file_path in file_paths:
            parsed = self.parser.parse_file(file_path)
            hooks.extend(parsed.get("hooks", []))

        return list(set(hooks))
