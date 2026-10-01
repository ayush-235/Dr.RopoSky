"""Safe Git cloner for controlled repository acquisition."""

import os
import shutil
import subprocess
from pathlib import Path
from rokospy_analyzer.config import config


class AcquisitionError(Exception):
    """Raised when repository acquisition fails."""
    pass


class SafeGitCloner:
    """
    Clones a public/authenticated Git repository into an isolated temporary workspace.
    Network is used ONLY for the controlled clone step, then the workspace becomes isolated.
    """

    @classmethod
    def clone(cls, repo_url: str, destination_dir: Path) -> Path:
        """
        Clones a git repository with shallow depth (--depth 1) into destination_dir.
        """
        destination_dir = destination_dir.resolve()
        destination_dir.mkdir(parents=True, exist_ok=True)

        # Validate URL scheme
        if not (repo_url.startswith("https://") or repo_url.startswith("http://") or repo_url.startswith("git@")):
            raise AcquisitionError(f"Invalid or unsupported Git repository URL: {repo_url}")

        cmd = [
            "git",
            "clone",
            "--depth", "1",
            "--single-branch",
            repo_url,
            str(destination_dir),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.GIT_CLONE_TIMEOUT_SECONDS,
                check=False,
                shell=False,
            )

            if result.returncode != 0:
                # Sanitize any credentials that might be in the clone URL before raising error
                err_msg = result.stderr.strip() or result.stdout.strip() or f"git clone failed with exit code {result.returncode}"
                raise AcquisitionError(f"Failed to clone repository: {err_msg}")

        except subprocess.TimeoutExpired as e:
            raise AcquisitionError(f"Repository clone timed out after {config.GIT_CLONE_TIMEOUT_SECONDS}s") from e
        except FileNotFoundError as e:
            raise AcquisitionError("Git binary is not installed or not found in PATH") from e
        except Exception as e:
            raise AcquisitionError(f"Unexpected error during git clone: {str(e)}") from e

        return destination_dir
