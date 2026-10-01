"""Projects & Re-scan API routes."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.schemas.errors import APIErrorDetail, APIErrorResponse
from app.services.persistence_service import (
    get_comparison_by_scan,
    get_project_scans,
    get_scan_comparison,
    rescan_project,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["projects"])


@router.post(
    "/projects/{project_id}/rescan",
    responses={
        400: {"model": APIErrorResponse},
        404: {"model": APIErrorResponse},
        500: {"model": APIErrorResponse},
    },
)
async def trigger_project_rescan(project_id: str) -> Dict[str, Any]:
    """Trigger a re-scan of a project, compare with the previous scan, and persist the delta."""
    try:
        rescan_data = rescan_project(project_id)
        return rescan_data
    except ValueError as e:
        msg = str(e)
        status_code = 404 if "not found" in msg.lower() else 400
        raise HTTPException(
            status_code=status_code,
            detail=APIErrorDetail(
                code="RESCAN_FAILED",
                message=msg,
            ).model_dump(),
        )
    except Exception as e:
        logger.error("Error executing project rescan for %s: %s", project_id, e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=APIErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred during project re-scan.",
            ).model_dump(),
        )


@router.get(
    "/projects/{project_id}/scans",
    responses={
        404: {"model": APIErrorResponse},
        500: {"model": APIErrorResponse},
    },
)
async def get_project_scan_history(
    project_id: str,
    limit: int = Query(default=20, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Retrieve scan history list for a specific project."""
    try:
        scans = get_project_scans(project_id, limit=limit)
        return scans
    except Exception as e:
        logger.error("Error retrieving scans for project %s: %s", project_id, e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=APIErrorDetail(
                code="RETRIEVE_SCANS_FAILED",
                message="Failed to retrieve scan history.",
            ).model_dump(),
        )


@router.get(
    "/scans/{scan_id}/comparison",
    responses={
        404: {"model": APIErrorResponse},
        500: {"model": APIErrorResponse},
    },
)
async def get_scan_comparison_endpoint(scan_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the comparison delta linked to a specific scan."""
    try:
        comparison = get_comparison_by_scan(scan_id)
        if not comparison:
            raise HTTPException(
                status_code=404,
                detail=APIErrorDetail(
                    code="COMPARISON_NOT_FOUND",
                    message=f"No comparison record found for scan {scan_id}.",
                ).model_dump(),
            )
        return comparison
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving comparison for scan %s: %s", scan_id, e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=APIErrorDetail(
                code="RETRIEVE_COMPARISON_FAILED",
                message="Failed to retrieve comparison record.",
            ).model_dump(),
        )


@router.get(
    "/comparisons/{comparison_id}",
    responses={
        404: {"model": APIErrorResponse},
        500: {"model": APIErrorResponse},
    },
)
async def get_comparison_by_id_endpoint(comparison_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a comparison record by its unique ID."""
    try:
        comparison = get_scan_comparison(comparison_id)
        if not comparison:
            raise HTTPException(
                status_code=404,
                detail=APIErrorDetail(
                    code="COMPARISON_NOT_FOUND",
                    message=f"Comparison {comparison_id} not found.",
                ).model_dump(),
            )
        return comparison
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving comparison %s: %s", comparison_id, e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=APIErrorDetail(
                code="RETRIEVE_COMPARISON_FAILED",
                message="Failed to retrieve comparison.",
            ).model_dump(),
        )
