import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any


class TargetBootstrapService:

    def __init__(self, registry_root: str):
        self.registry_root = Path(registry_root)
        self.index = self._load_index()

    def _load_index(self):
        with open(self.registry_root / "index.json") as f:
            return json.load(f)

    def bootstrap(
        self,
        framework: str,
        language: str,
        engine: str,
        workspace_path: str,
        variables: Dict[str, str]
    ):
        manifest_file = self._resolve_manifest(framework, language, engine)
        manifest = self._load_manifest(manifest_file)

        resolved_vars = self._resolve_variables(manifest, variables)

        self._create_folders(manifest, workspace_path)
        self._create_files(manifest, workspace_path, resolved_vars)

    def _resolve_manifest(self, framework, language, engine):
        try:
            return (
                self.registry_root
                / "manifests"
                / self.index[framework][language][engine]
            )
        except KeyError:
            raise Exception("Unsupported target combination")

    def _load_manifest(self, path: Path):
        with open(path) as f:
            return json.load(f)

    def _resolve_variables(self, manifest, provided_vars):
        resolved = {}
        for var, config in manifest.get("variables", {}).items():
            if var in provided_vars:
                resolved[var] = provided_vars[var]
            elif config.get("required") and "default" not in config:
                raise Exception(f"Missing required variable: {var}")
            else:
                resolved[var] = config.get("default")
        return resolved

    def _create_folders(self, manifest, workspace):
        for folder in manifest.get("folders", []):
            folder_path = Path(workspace) / folder["path"]
            folder_path.mkdir(parents=True, exist_ok=True)

            if folder.get("gitkeep"):
                (folder_path / ".gitkeep").touch()

    def _create_files(self, manifest, workspace, variables):
        for file_def in manifest.get("files", []):
            file_path = Path(workspace) / file_def["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if file_def["type"] == "fragment":
                content = self._load_fragment(file_def["source"])
            elif file_def["type"] == "inline":
                content = file_def["content"]
            else:
                raise Exception("Unsupported file type")

            rendered = self._render_template(content, variables)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(rendered)

    def _load_fragment(self, fragment_name):
        fragment_path = self.registry_root / "fragments" / fragment_name
        with open(fragment_path, encoding="utf-8") as f:
            return f.read()

    def _render_template(self, content: str, variables: Dict[str, str]):
        for key, value in variables.items():
            content = content.replace(f"{{{{{key}}}}}", value)
        return content
