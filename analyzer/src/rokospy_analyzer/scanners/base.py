"""Abstract Base Scanner contract for Rokospy Analyzer adapters."""

import abc
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from rokospy_analyzer.config import config
from rokospy_analyzer.models.discovery import ProjectDiscovery
from rokospy_analyzer.models.finding import NormalizedFinding
from rokospy_analyzer.models.report import ScannerStatusEnum


class BaseScanner(abc.ABC):
    """Abstract interface that all static & security scanner adapters must implement."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique identifier name for this scanner adapter."""
        pass

    @property
    @abc.abstractmethod
    def supported_languages(self) -> List[str]:
        """List of supported languages (e.g. ['Python', 'JavaScript', 'TypeScript', 'All'])."""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Returns True if the required executable/binary or module is present in the system."""
        pass

    @abc.abstractmethod
    def is_applicable(self, discovery: ProjectDiscovery) -> bool:
        """Returns True if this scanner is relevant for the detected project languages/manifests."""
        pass

    @abc.abstractmethod
    def run(self, workspace_path: Path, discovery: ProjectDiscovery) -> Tuple[ScannerStatusEnum, List[NormalizedFinding], Optional[str]]:
        """
        Executes the scanner against the workspace path under strict timeouts and sandboxing.
        Returns (status, list_of_normalized_findings, error_message_if_any).
        """
        pass

    def _execute_subprocess(
        self,
        cmd: List[str],
        cwd: Path,
        timeout_seconds: Optional[int] = None,
    ) -> Tuple[int, str, str]:
        """
        Executes a controlled subprocess with shell=False, strict timeout, and output capture.
        """
        timeout = timeout_seconds or config.SCANNER_TIMEOUT_SECONDS
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Scanner '{self.name}' timed out after {timeout} seconds"
        except FileNotFoundError:
            return -2, "", f"Scanner binary '{cmd[0]}' not found in PATH"
        except Exception as e:
            return -3, "", f"Execution error in '{self.name}': {str(e)}"
