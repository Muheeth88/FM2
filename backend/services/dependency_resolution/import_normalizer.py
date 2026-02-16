from typing import List, Optional
from services.dependency_resolution.path_resolver import PathResolver


class ImportNormalizer:
    """
    Normalizes imports into repository-relative file paths.
    Filters out external dependencies.
    """

    def __init__(self, repo_root: str, language: str):
        self.repo_root = repo_root
        self.language = language
        self.resolver = PathResolver(repo_root)

    # ---------------------------------------------------------
    # PUBLIC ENTRY
    # ---------------------------------------------------------

    def normalize_imports(self, imports: List[str], current_file: str) -> List[str]:

        normalized = []

        for imp in imports:

            resolved = self.resolver.resolve(
                import_path=imp,
                current_file=current_file,
                language=self.language
            )

            if resolved:
                normalized.append(self._clean_path(resolved))

        return list(set(normalized))

    # ---------------------------------------------------------
    # Normalize path formatting
    # ---------------------------------------------------------

    def _clean_path(self, path: str) -> str:
        return path.replace("\\", "/")
