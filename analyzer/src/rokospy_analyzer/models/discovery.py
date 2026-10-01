"""Project discovery and inspection models."""

from pathlib import Path
from typing import List, Set, Dict, Any
from pydantic import BaseModel, Field


class ProjectDiscovery(BaseModel):
    project_name: str
    source_type: str = Field(..., description="github | zip | local")
    root_path: Path
    detected_languages: List[str] = Field(default_factory=list)
    manifests_found: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    all_files: List[str] = Field(default_factory=list, description="Relative paths of all valid source files")
    total_file_count: int = 0
    total_size_bytes: int = 0
    has_git_history: bool = False
    
    # Essentials flags
    has_readme: bool = False
    has_gitignore: bool = False
    has_env_example: bool = False
    has_license: bool = False
    has_tests: bool = False

    model_config = {
        "arbitrary_types_allowed": True,
    }
