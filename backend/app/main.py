"""Rokospy Backend — FastAPI Application."""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import backend_config
from app.api.router import api_v1_router
from app.schemas.errors import APIErrorDetail, APIErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    from app.db.supabase_client import supabase_store
    persistence_mode = "Supabase" if supabase_store.is_live else "Local Fallback"
    logger.info("Rokospy Backend starting (v%s)", backend_config.VERSION)
    logger.info("Persistence: %s", persistence_mode)
    yield
    logger.info("Rokospy Backend shutting down")


app = FastAPI(
    title=backend_config.PROJECT_NAME,
    version=backend_config.VERSION,
    lifespan=lifespan,
    docs_url=f"{backend_config.API_V1_PREFIX}/docs",
    openapi_url=f"{backend_config.API_V1_PREFIX}/openapi.json",
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=backend_config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# --- API Router ---
app.include_router(api_v1_router, prefix=backend_config.API_V1_PREFIX)


# --- Global Exception Handlers ---
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content=APIErrorResponse(
            error=APIErrorDetail(
                code="HTTP_ERROR",
                message=str(exc.detail),
            )
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=APIErrorResponse(
            error=APIErrorDetail(
                code="VALIDATION_ERROR",
                message=str(exc),
            )
        ).model_dump(),
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content=APIErrorResponse(
            error=APIErrorDetail(
                code="NOT_FOUND",
                message="The requested resource was not found",
            )
        ).model_dump(),
    )


@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc):
    return JSONResponse(
        status_code=405,
        content=APIErrorResponse(
            error=APIErrorDetail(
                code="METHOD_NOT_ALLOWED",
                message="HTTP method not allowed for this endpoint",
            )
        ).model_dump(),
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error("Unhandled server error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content=APIErrorResponse(
            error=APIErrorDetail(
                code="INTERNAL_ERROR",
                message="An internal server error occurred",
            )
        ).model_dump(),
    )

