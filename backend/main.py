"""
LexGuard One — FastAPI Application Entry Point.

Production-grade adversarial multi-agent AI contract intelligence system.
Configures middleware, security headers, CORS, rate limiting,
structured logging, and serves the React frontend.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.models.schemas import HealthResponse
from backend.routers.analyze import router as analyze_router
from backend.utils.gemini_client import initialize_gemini

# Configure structured JSON logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("lexguard.main")

# Rate limiter: 10 requests/minute per IP
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager — startup and shutdown.

    Initializes Gemini SDK and logs startup.

    Args:
        app: The FastAPI application instance.
    """
    logger.info(json.dumps({
        "service": "main", "operation": "startup",
        "status": "initializing",
    }))

    # Initialize Gemini API
    try:
        initialize_gemini()
    except ValueError as exc:
        logger.warning(json.dumps({
            "service": "main", "operation": "startup",
            "warning": str(exc),
        }))

    # Wire Google Cloud Logging when running on GCP
    try:
        import google.cloud.logging as gcp_logging
        if os.environ.get("GOOGLE_CLOUD_PROJECT"):
            gcp_client = gcp_logging.Client()
            gcp_client.setup_logging()
            logger.info(json.dumps({
                "service": "main", "operation": "cloud_logging",
                "status": "attached",
            }))
    except Exception as gcp_exc:
        logger.warning(json.dumps({
            "service": "main", "operation": "cloud_logging",
            "warning": f"Cloud Logging not attached: {gcp_exc}",
        }))

    logger.info(json.dumps({
        "service": "main", "operation": "startup",
        "status": "ready", "version": "1.0.0",
    }))

    yield

    logger.info(json.dumps({
        "service": "main", "operation": "shutdown",
        "status": "complete",
    }))


app = FastAPI(
    title="LexGuard One",
    description=(
        "Adversarial multi-agent AI contract intelligence system. "
        "Analyzes legal documents clause-by-clause using a "
        "Risk/Defense/Verdict agent pipeline."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
allowed_origins = os.environ.get(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(
    request: Request, call_next
) -> Response:
    """Add security headers to all responses.

    Args:
        request: Incoming HTTP request.
        call_next: Next middleware handler.

    Returns:
        Response with security headers added.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Include API routes
app.include_router(analyze_router, tags=["analysis"])


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for Cloud Run probes.

    Returns:
        HealthResponse with status and version.
    """
    return HealthResponse(status="ok", version="1.0.0")


# Serve React frontend static files
frontend_dist_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "frontend", "dist"
)
if os.path.exists(frontend_dist_path):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(frontend_dist_path, "assets")),
        name="static_assets",
    )

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str) -> FileResponse:
        """Serve the React SPA for all non-API routes.

        Args:
            full_path: Requested path.

        Returns:
            The index.html file for client-side routing.
        """
        file_path = os.path.join(frontend_dist_path, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(
            os.path.join(frontend_dist_path, "index.html")
        )
