"""File and directory filtering rules for Rokospy Analyzer."""

from pathlib import Path
from typing import List, Tuple
from rokospy_analyzer.config import config


class FileFilter:
    """Filters out generated files, vendor trees, and media assets while preserving code & manifests."""

    @staticmethod
    def is_dir_excluded(dir_name: str) -> bool:
        """Returns True if the directory name matches excluded vendor/generated directory sets."""
        return dir_name in config.EXCLUDED_DIRS or dir_name.startswith(".git")

    @staticmethod
    def is_file_analyzable(file_path: Path, root_path: Path) -> Tuple[bool, str]:
        """
        Determines whether a file should be included in static analysis.
        Returns (is_valid, reason_if_excluded).
        """
        try:
            rel_path = file_path.relative_to(root_path)
        except ValueError:
            return False, "File outside root directory"

        # Check path parts against excluded directories
        for part in rel_path.parts[:-1]:
            if FileFilter.is_dir_excluded(part):
                return False, f"Inside excluded directory: {part}"

        # Check extension
        ext = file_path.suffix.lower()
        if ext in config.EXCLUDED_EXTENSIONS:
            return False, f"Excluded extension: {ext}"

        # Check file size
        try:
            size = file_path.stat().st_size
            if size > config.MAX_FILE_SIZE_BYTES:
                return False, f"File exceeds size limit: {size} bytes"
            if size == 0:
                # Still allow empty files if they are essentials like .gitignore or README
                pass
        except OSError as e:
            return False, f"Filesystem stat error: {str(e)}"

        return True, "OK"

    @classmethod
    def collect_analyzable_files(cls, root_path: Path) -> List[Path]:
        """Walks the root directory safely and returns all analyzable files."""
        valid_files: List[Path] = []
        if not root_path.exists() or not root_path.is_dir():
            return valid_files

        for item in root_path.rglob("*"):
            if item.is_file():
                valid, _ = cls.is_file_analyzable(item, root_path)
                if valid:
                    valid_files.append(item)

        return valid_files
