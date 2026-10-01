"""Workspace management and acquisition orchestrator."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from rokospy_analyzer.acquisition.git_cloner import SafeGitCloner, AcquisitionError
from rokospy_analyzer.acquisition.zip_extractor import SafeZipExtractor, ExtractionError


class ManagedWorkspace:
    """
    Context manager that acquires and prepares an isolated ephemeral workspace
    from a local directory, ZIP archive, or Git URL, and deterministically cleans it up.
    """

    def __init__(self, target_input: str, custom_tmp_dir: Optional[Path] = None):
        self.target_input = target_input.strip()
        self.custom_tmp_dir = custom_tmp_dir
        self._temp_dir_obj: Optional[tempfile.TemporaryDirectory] = None
        self.workspace_path: Optional[Path] = None
        self.source_type: str = "local"
        self.project_name: str = "project"

    def __enter__(self) -> Tuple[Path, str, str]:
        """
        Acquires target and returns (workspace_path, source_type, project_name).
        """
        self._temp_dir_obj = tempfile.TemporaryDirectory(dir=self.custom_tmp_dir, prefix="rokospy_ws_")
        temp_root = Path(self._temp_dir_obj.name).resolve()

        target = self.target_input

        # 1. Git Repository URL
        if target.startswith("http://") or target.startswith("https://") or target.startswith("git@"):
            self.source_type = "github"
            repo_name = target.rstrip("/").split("/")[-1]
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
            self.project_name = repo_name or "github-project"
            
            clone_dest = temp_root / "repo"
            self.workspace_path = SafeGitCloner.clone(target, clone_dest)
            return self.workspace_path, self.source_type, self.project_name

        # 2. Local ZIP Archive
        target_path = Path(target).resolve()
        if target_path.is_file() and (target_path.suffix.lower() == ".zip"):
            self.source_type = "zip"
            self.project_name = target_path.stem
            extract_dest = temp_root / "extracted"
            self.workspace_path = SafeZipExtractor.extract(target_path, extract_dest)
            return self.workspace_path, self.source_type, self.project_name

        # 3. Local Directory
        if target_path.is_dir():
            self.source_type = "local"
            self.project_name = target_path.name
            # Copy directory contents into isolated temp workspace for safety
            isolated_dest = temp_root / "source"
            isolated_dest.mkdir(parents=True, exist_ok=True)
            
            # Copy preserving files but skipping huge vendor dirs if they already exist
            for item in target_path.iterdir():
                dest_item = isolated_dest / item.name
                if item.is_dir():
                    if item.name in {".git", "node_modules", ".venv", "venv", "__pycache__"}:
                        continue
                    shutil.copytree(item, dest_item, symlinks=False, ignore_dangling_symlinks=True)
                elif item.is_file():
                    shutil.copy2(item, dest_item)

            self.workspace_path = isolated_dest
            return self.workspace_path, self.source_type, self.project_name

        raise AcquisitionError(f"Target input is neither a valid Git URL, ZIP file, nor existing directory: {target}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Deterministically cleans up the temporary analysis workspace."""
        if self._temp_dir_obj:
            try:
                self._temp_dir_obj.cleanup()
            except Exception:
                # Fallback forced cleanup on Windows if locked handles exist
                if self.workspace_path and self.workspace_path.parent.exists():
                    shutil.rmtree(self.workspace_path.parent, ignore_errors=True)
            self._temp_dir_obj = None
            self.workspace_path = None
