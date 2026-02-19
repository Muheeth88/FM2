import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List


class TargetBootstrapService:

    def __init__(self, registry_root: str):
        self.registry_root = Path(registry_root)
        self.index = self._load_index()

    # ============================================================
    # PUBLIC ENTRY
    # ============================================================

    def bootstrap(
        self,
        framework: str,
        language: str,
        engine: str,
        workspace_path: str,
        variables: Dict[str, str],
        execute_hooks: bool = True,
        dry_run: bool = False
    ) -> Dict[str, Any]:

        manifest_file = self._resolve_manifest(framework, language, engine)
        manifest = self._load_manifest(manifest_file)

        resolved_vars = self._resolve_variables(manifest, variables)

        report = {
            "status": "SUCCESS",
            "folders_created": [],
            "files_created": [],
            "files_overwritten": [],
            "post_install_commands_executed": [],
            "post_install_failures": []
        }

        try:
            self._create_folders(manifest, workspace_path, report, dry_run)
            self._create_files(manifest, workspace_path, resolved_vars, report, dry_run)

            # ✅ CI Support (handled via manifest files automatically)
            # Nothing special needed — manifest can define .github/workflows/*

            # ✅ Post-install hooks
            if execute_hooks and not dry_run:
                self._run_post_install_hooks(manifest, workspace_path, report)

        except Exception as e:
            report["status"] = "FAILED"
            report["error"] = str(e)

        return report

    def check_foundation(
        self,
        framework: str,
        language: str,
        engine: str,
        workspace_path: str
    ) -> Dict[str, Any]:
        """
        Checks if the target workspace already has the foundational files and folders.
        Returns a status and a list of missing items.
        """
        try:
            manifest_file = self._resolve_manifest(framework, language, engine)
            manifest = self._load_manifest(manifest_file)
        except Exception as e:
            return {"status": "ERROR", "error": f"Manifest not found: {str(e)}"}

        missing_folders = []
        missing_files = []

        workspace = Path(workspace_path)

        for folder in manifest.get("folders", []):
            folder_path = workspace / folder["path"]
            if not folder_path.exists() or not folder_path.is_dir():
                missing_folders.append(folder["path"])

        for file_def in manifest.get("files", []):
            file_path = workspace / file_def["path"]
            if not file_path.exists() or not file_path.is_file():
                missing_files.append(file_def["path"])

        is_complete = len(missing_folders) == 0 and len(missing_files) == 0

        return {
            "status": "SUCCESS" if is_complete else "MISSING",
            "is_complete": is_complete,
            "missing_folders": missing_folders,
            "missing_files": missing_files
        }

    # ============================================================
    # MANIFEST RESOLUTION
    # ============================================================

    def _load_index(self):
        with open(self.registry_root / "index.json") as f:
            return json.load(f)

    def _resolve_manifest(self, framework: str, language: str, engine: str):
        # Normalize keys for robust matching (lowercase, no spaces)
        f = framework.lower().replace(" ", "")
        l = language.lower().replace(" ", "")
        e = engine.lower().replace(" ", "")
        try:
            return (
                self.registry_root
                / "manifests"
                / self.index[f][l][e]
            )
        except KeyError:
            available = list(self.index.keys())
            raise Exception(f"Unsupported target combination: {f}/{l}/{e}. Available frameworks: {available}")

    def _load_manifest(self, path: Path):
        with open(path) as f:
            return json.load(f)

    # ============================================================
    # VARIABLE RESOLUTION
    # ============================================================

    def _resolve_variables(self, manifest, provided_vars):
        resolved = {}
        for var, config in manifest.get("variables", {}).items():
            if var in provided_vars:
                resolved[var] = provided_vars[var]
            elif config.get("required") and "default" not in config:
                raise Exception(f"Missing required variable: {var}")
            else:
                resolved[var] = config.get("default", "")
        return resolved

    # ============================================================
    # FOLDER CREATION
    # ============================================================

    def _create_folders(self, manifest, workspace, report, dry_run):
        for folder in manifest.get("folders", []):
            folder_path = Path(workspace) / folder["path"]

            if not dry_run:
                folder_path.mkdir(parents=True, exist_ok=True)

                if folder.get("gitkeep"):
                    (folder_path / ".gitkeep").touch()

            report["folders_created"].append(folder["path"])

    # ============================================================
    # FILE CREATION (CI SUPPORTED HERE)
    # ============================================================

    def _create_files(self, manifest, workspace, variables, report, dry_run):

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

            if file_path.exists():
                if file_def.get("overwrite", False):
                    report["files_overwritten"].append(file_def["path"])
                else:
                    continue
            else:
                report["files_created"].append(file_def["path"])

            if not dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(rendered)

    # ============================================================
    # POST-INSTALL HOOKS
    # ============================================================

    def _run_post_install_hooks(self, manifest, workspace, report):

        commands = manifest.get("post_install", [])

        for cmd in commands:
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=workspace,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=600
                )

                if result.returncode != 0:
                    report["post_install_failures"].append({
                        "command": cmd,
                        "error": result.stderr.decode()
                    })
                else:
                    report["post_install_commands_executed"].append(cmd)

            except Exception as e:
                report["post_install_failures"].append({
                    "command": cmd,
                    "error": str(e)
                })

    # ============================================================
    # TEMPLATE SUPPORT
    # ============================================================

    def _load_fragment(self, fragment_name):
        fragment_path = self.registry_root / "fragments" / fragment_name
        with open(fragment_path, encoding="utf-8") as f:
            return f.read()

    def _render_template(self, content: str, variables: Dict[str, str]):
        for key, value in variables.items():
            content = content.replace(f"{{{{{key}}}}}", value)
        return content
