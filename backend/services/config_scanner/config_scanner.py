import os


class ConfigScanner:

    CONFIG_EXTENSIONS = [
        ".properties",
        ".xml",
        ".json",
        ".yaml",
        ".yml",
        ".env",
        ".ini",
        ".toml"
    ]

    @staticmethod
    def scan(repo_root):

        results = []

        for root, _, files in os.walk(repo_root):
            for file in files:
                for ext in ConfigScanner.CONFIG_EXTENSIONS:
                    if file.endswith(ext):
                        results.append({
                            "file_path": os.path.join(root, file),
                            "type": ext
                        })

        return results
