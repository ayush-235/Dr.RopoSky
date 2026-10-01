"""Pytest configuration and shared fixtures for Rokospy Analyzer tests."""

import sys
from pathlib import Path
import pytest

# Ensure analyzer/src is in sys.path for test imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
