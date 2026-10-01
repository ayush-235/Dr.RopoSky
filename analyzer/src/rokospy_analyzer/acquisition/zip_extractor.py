"""Safe ZIP extraction with Zip Slip defense and quota enforcement."""

import os
import zipfile
from pathlib import Path
from rokospy_analyzer.config import config


class ExtractionError(Exception):
    """Raised when an archive fails validation or extraction."""
    pass


class SafeZipExtractor:
    """Extracts ZIP archives while strictly preventing path traversal and zip bombs."""

    @classmethod
    def extract(cls, zip_path: Path, destination_dir: Path) -> Path:
        """
        Safely extracts a ZIP archive into destination_dir.
        Enforces:
        - Absolute path / traversal rejection (Zip Slip).
        - Cumulative file size limit (Zip bomb protection).
        - Maximum file count limit.
        """
        if not zip_path.exists() or not zip_path.is_file():
            raise ExtractionError(f"ZIP file not found: {zip_path}")

        destination_dir = destination_dir.resolve()
        destination_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                infolist = zf.infolist()
                
                # Check file count quota
                if len(infolist) > config.MAX_FILE_COUNT:
                    raise ExtractionError(
                        f"Archive exceeds maximum file count limit: {len(infolist)} > {config.MAX_FILE_COUNT}"
                    )

                # Check cumulative uncompressed size quota
                total_uncompressed_bytes = sum(info.file_size for info in infolist)
                max_bytes = config.MAX_EXTRACTED_SIZE_MB * 1024 * 1024
                if total_uncompressed_bytes > max_bytes:
                    raise ExtractionError(
                        f"Archive uncompressed size exceeds limit: {total_uncompressed_bytes} bytes > {max_bytes} bytes"
                    )

                for member in infolist:
                    # Reject dangerous paths
                    cls._validate_member_path(member.filename, destination_dir)

                # Extract safely
                for member in infolist:
                    target_path = (destination_dir / member.filename).resolve()
                    if not cls._is_safe_path(destination_dir, target_path):
                        raise ExtractionError(f"Dangerous path detected during extraction: {member.filename}")

                    if member.is_dir():
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as source_file, open(target_path, "wb") as dest_file:
                            # Stream in 64KB chunks
                            while chunk := source_file.read(65536):
                                dest_file.write(chunk)

        except zipfile.BadZipFile as e:
            raise ExtractionError(f"Invalid or corrupted ZIP archive: {str(e)}") from e

        return destination_dir

    @staticmethod
    def _is_safe_path(base_dir: Path, target_path: Path) -> bool:
        """Verifies that target_path is strictly within base_dir."""
        try:
            return target_path.resolve().is_relative_to(base_dir.resolve())
        except (ValueError, AttributeError):
            # Fallback for Python versions or OS path resolution edge cases
            base_str = str(base_dir.resolve())
            target_str = str(target_path.resolve())
            return target_str.startswith(base_str + os.sep) or target_str == base_str

    @classmethod
    def _validate_member_path(cls, filename: str, destination_dir: Path) -> None:
        """Rejects paths containing traversal segments or absolute path indicators."""
        # Check raw filename string
        if filename.startswith("/") or filename.startswith("\\") or (len(filename) > 1 and filename[1] == ":"):
            raise ExtractionError(f"Absolute path in archive rejected: {filename}")

        parts = Path(filename).parts
        if ".." in parts:
            raise ExtractionError(f"Path traversal sequence in archive rejected: {filename}")

        # Check resolved target path
        target = (destination_dir / filename).resolve()
        if not cls._is_safe_path(destination_dir, target):
            raise ExtractionError(f"Path traversal attempt rejected: {filename}")
