"""Persistence orchestration service for Dr.RopoSky scans, projects, and rescans."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from rokospy_analyzer.models.report import AnalysisReport
from app.db.supabase_client import supabase_store
from app.services.analysis_service import run_analysis, validate_github_url
from app.services.comparison_service import ComparisonEngine

logger = logging.getLogger(__name__)


def save_analysis_report(
    report_data: Dict[str, Any],
    source_type: str,
    source_url: Optional[str] = None,
    project_name: Optional[str] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Persists project and scan record in Supabase / fallback memory store.
    Modifies report_data in-place to include project_id and scan_id.
    """
    metadata = report_data.get("project") or {}
    name = (
        project_name
        or metadata.get("name")
        or (source_url.split("/")[-1].replace(".git", "") if source_url else None)
        or "Unnamed Project"
    )

    if not source_url and metadata.get("target_url"):
        source_url = metadata.get("target_url")

    # Clean / validate url if git
    if source_type == "git" and source_url:
        try:
            source_url = validate_github_url(source_url)
        except Exception:
            pass

    # 1. Get or create project
    project = supabase_store.get_or_create_project(
        name=name,
        source_type=source_type,
        source_url=source_url,
    )
    project_id = project["id"]
    report_data["project_id"] = project_id

    # 2. Persist scan and findings
    scan = supabase_store.create_scan(
        project_id=project_id,
        report_data=report_data,
        status="completed",
    )
    scan_id = scan["id"]
    report_data["scan_id"] = scan_id

    logger.info("Persisted scan %s for project %s (%s)", scan_id, name, project_id)
    return project, scan


def rescan_project(project_id: str) -> Dict[str, Any]:
    """
    Executes a re-scan of an existing Git project, compares with the previous scan,
    and returns both the new report and the deterministic comparison results.
    """
    project = supabase_store.get_project(project_id)
    if not project:
        raise ValueError(f"Project with ID '{project_id}' not found.")

    source_type = project.get("source_type")
    source_url = project.get("source_url")

    if source_type != "git" or not source_url:
        raise ValueError(
            "Automated one-click re-scan is only available for Git repositories. "
            "For ZIP uploads, please upload the new ZIP archive."
        )

    # Validate Git URL
    validated_url = validate_github_url(source_url)

    # Get the previous completed scan
    prev_scan_record = supabase_store.get_latest_completed_scan(project_id)
    if not prev_scan_record:
        raise ValueError("No previous completed scan found to compare against.")

    # Run analysis on fresh repo state
    logger.info("Executing rescan for project %s (%s)", project.get("name"), validated_url)
    current_report_data = run_analysis(validated_url)

    # Persist the new scan
    _, current_scan = save_analysis_report(
        report_data=current_report_data,
        source_type="git",
        source_url=validated_url,
        project_name=project.get("name"),
    )

    # Compare with previous scan using deterministic ComparisonEngine
    prev_report_raw = prev_scan_record.get("raw_report") or {}
    prev_report_obj = AnalysisReport.model_validate(prev_report_raw)
    curr_report_obj = AnalysisReport.model_validate(current_report_data)

    comparison_result = ComparisonEngine.compare_reports(prev_report_obj, curr_report_obj)
    comparison_dict = comparison_result.model_dump()

    # Persist comparison record
    comparison_record = supabase_store.create_scan_comparison(
        project_id=project_id,
        previous_scan_id=prev_scan_record["id"],
        current_scan_id=current_scan["id"],
        comparison_dict=comparison_dict,
    )
    comparison_dict["id"] = comparison_record["id"]

    return {
        "project": project,
        "previous_scan_id": prev_scan_record["id"],
        "current_scan_id": current_scan["id"],
        "current_report": current_report_data,
        "comparison": comparison_dict,
    }


def get_project_scans(project_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve scan history for a project."""
    return supabase_store.get_project_scans(project_id, limit=limit)


def get_scan_comparison(comparison_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a comparison by ID."""
    return supabase_store.get_scan_comparison(comparison_id)


def get_comparison_by_scan(scan_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve comparison corresponding to a given scan."""
    return supabase_store.get_comparison_by_current_scan(scan_id)
