import os
from typing import Optional


class PathResolver:
    """
    Resolves import strings to actual repository-relative file paths.
    """

    def __init__(self, repo_root: str):
        self.repo_root = repo_root

    # ---------------------------------------------------------
    # PUBLIC ENTRY
    # ---------------------------------------------------------

    def resolve(self, import_path: str, current_file: str, language: str) -> Optional[str]:

        if language.lower() in ["typescript", "javascript", "ts", "js"]:
            return self._resolve_ts(import_path, current_file)

        if language.lower() == "python":
            return self._resolve_python(import_path)

        if language.lower() == "java":
            return self._resolve_java(import_path)

        return None

    # ---------------------------------------------------------
    # TYPESCRIPT / JAVASCRIPT
    # ---------------------------------------------------------

    def _resolve_ts(self, import_path: str, current_file: str) -> Optional[str]:

        # Handle relative imports: ./ or ../
        if import_path.startswith("."):

            base_dir = os.path.dirname(current_file)
            full_path = os.path.normpath(os.path.join(base_dir, import_path))

            return self._find_existing_file(full_path)

        # Non-relative → likely external lib
        return None

    # ---------------------------------------------------------
    # PYTHON
    # ---------------------------------------------------------

    def _resolve_python(self, import_path: str) -> Optional[str]:

        # Convert module path to file path
        # e.g., utils.helper → utils/helper.py

        file_path = import_path.replace(".", os.sep) + ".py"

        abs_path = os.path.join(self.repo_root, file_path)

        if os.path.exists(abs_path):
            return file_path

        return None

    # ---------------------------------------------------------
    # JAVA
    # ---------------------------------------------------------

    def _resolve_java(self, import_path: str) -> Optional[str]:

        # Convert package path to file path
        # e.g., com.project.utils.Helper
        # → com/project/utils/Helper.java

        file_path = import_path.replace(".", os.sep) + ".java"

        for root, _, files in os.walk(self.repo_root):
            if file_path in [os.path.join(root, f).replace(self.repo_root + os.sep, "")
                             for f in files]:
                return file_path

        return None

    # ---------------------------------------------------------
    # File existence resolution
    # ---------------------------------------------------------

    def _find_existing_file(self, base_path: str) -> Optional[str]:

        extensions = [".ts", ".tsx", ".js", ".jsx"]

        for ext in extensions:
            candidate = base_path + ext
            abs_path = os.path.join(self.repo_root, candidate)
            if os.path.exists(abs_path):
                return candidate

        # Handle index.ts resolution
        index_candidate = os.path.join(base_path, "index.ts")
        abs_index = os.path.join(self.repo_root, index_candidate)
        if os.path.exists(abs_index):
            return index_candidate

        return None
