"""Pytest fixtures for backend test suite."""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add analyzer/src and backend to sys.path
backend_root = Path(__file__).parent.parent
analyzer_src = backend_root.parent / "analyzer" / "src"

if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
if str(analyzer_src) not in sys.path:
    sys.path.insert(0, str(analyzer_src))

from app.main import app


@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    return TestClient(app)
