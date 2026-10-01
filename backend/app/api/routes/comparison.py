"""Comparison route — POST /api/v1/compare."""

from fastapi import APIRouter, HTTPException
from app.schemas.comparison import ComparisonReport, ComparisonRequest
from app.schemas.errors import APIErrorDetail, APIErrorResponse
from app.services.comparison_service import ComparisonEngine

router = APIRouter(tags=["comparison"])


@router.post(
    "/compare",
    response_model=ComparisonReport,
    responses={
        400: {"model": APIErrorResponse},
        422: {"model": APIErrorResponse},
        500: {"model": APIErrorResponse},
    },
)
async def compare_reports_endpoint(request: ComparisonRequest) -> ComparisonReport:
    """Deterministically compare two AnalysisReports to track progress, score deltas, and fixed/new/remaining findings."""
    if not request.previous_report or not request.current_report:
        raise HTTPException(
            status_code=400,
            detail=APIErrorDetail(
                code="INVALID_PAYLOAD",
                message="Both previous_report and current_report must be provided for comparison.",
            ).model_dump(),
        )

    try:
        comparison = ComparisonEngine.compare_reports(
            request.previous_report, request.current_report
        )
        return comparison
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=APIErrorDetail(
                code="COMPARISON_FAILED",
                message="Comparison engine encountered an error while processing reports.",
            ).model_dump(),
        )
