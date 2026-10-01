"""Analysis endpoint — POST /analyze."""

import logging
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import backend_config
from app.schemas.errors import APIErrorDetail, APIErrorResponse
from app.services.analysis_service import run_analysis, validate_github_url
from app.services.persistence_service import save_analysis_report

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])

_MAX_UPLOAD_BYTES = backend_config.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@router.post(
    "/analyze",
    response_model=None,
    responses={
        400: {"model": APIErrorResponse},
        413: {"model": APIErrorResponse},
        422: {"model": APIErrorResponse},
        500: {"model": APIErrorResponse},
    },
)
async def analyze_project(
    github_url: Optional[str] = Form(default=None),
    zip_file: Optional[UploadFile] = File(default=None),
):
    """Analyze a software project from a GitHub URL or uploaded ZIP file.

    Exactly one of github_url or zip_file must be provided.
    """
    # --- Input Validation: exactly one source ---
    has_url = github_url is not None and github_url.strip() != ""
    has_file = zip_file is not None and zip_file.filename

    if has_url and has_file:
        raise HTTPException(
            status_code=400,
            detail=APIErrorDetail(
                code="INVALID_SOURCE",
                message="Provide exactly one of github_url or zip_file, not both",
            ).model_dump(),
        )

    if not has_url and not has_file:
        raise HTTPException(
            status_code=400,
            detail=APIErrorDetail(
                code="INVALID_SOURCE",
                message="Provide exactly one of github_url or zip_file",
            ).model_dump(),
        )

    # --- GitHub URL path ---
    if has_url:
        try:
            validated_url = validate_github_url(github_url.strip())
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=APIErrorDetail(
                    code="INVALID_URL",
                    message=str(e),
                ).model_dump(),
            )

        try:
            result = run_analysis(validated_url)
            try:
                save_analysis_report(result, source_type="git", source_url=validated_url)
            except Exception as e:
                logger.warning("Failed to persist Git analysis report: %s", e)
            return result
        except RuntimeError as e:
            raise HTTPException(
                status_code=500,
                detail=APIErrorDetail(
                    code="ANALYSIS_FAILED",
                    message=str(e),
                ).model_dump(),
            )

    # --- ZIP Upload path ---
    if has_file:
        # Validate file extension
        filename = zip_file.filename or ""
        if not filename.lower().endswith(".zip"):
            raise HTTPException(
                status_code=400,
                detail=APIErrorDetail(
                    code="INVALID_FILE_TYPE",
                    message="Only .zip files are accepted",
                ).model_dump(),
            )

        # Read and validate size
        max_upload_bytes = backend_config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        content = await zip_file.read()
        if len(content) > max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=APIErrorDetail(
                    code="FILE_TOO_LARGE",
                    message=f"Upload exceeds maximum size of {backend_config.MAX_UPLOAD_SIZE_MB} MB",
                ).model_dump(),
            )

        # Save to temp file and run analysis
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".zip", delete=False, prefix="rokospy_upload_"
            ) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)

            result = run_analysis(str(tmp_path))
            try:
                proj_name = filename.rsplit(".", 1)[0]
                save_analysis_report(result, source_type="zip", project_name=proj_name)
            except Exception as e:
                logger.warning("Failed to persist ZIP analysis report: %s", e)
            return result
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=APIErrorDetail(
                    code="INVALID_ARCHIVE",
                    message=str(e),
                ).model_dump(),
            )
        except RuntimeError as e:
            raise HTTPException(
                status_code=500,
                detail=APIErrorDetail(
                    code="ANALYSIS_FAILED",
                    message=str(e),
                ).model_dump(),
            )
        finally:
            # Deterministic cleanup
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    logger.warning("Failed to clean up temp file: %s", tmp_path.name)
