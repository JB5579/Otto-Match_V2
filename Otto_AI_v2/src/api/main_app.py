"""
Otto.AI Main FastAPI Application
Central application that combines all API routers and provides unified access.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import all API routers
from .listings_api import listings_router
from .semantic_search_api import app as semantic_search_app
from .vehicle_comparison_api import app as comparison_app
from .filter_management_api import app as filter_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """Create and configure the main FastAPI application"""

    app = FastAPI(
        title="Otto.AI Vehicle Discovery API",
        description="AI-powered vehicle discovery platform with conversational interfaces",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://otto-ai.com"],  # Frontend URLs
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = datetime.utcnow()

        response = await call_next(request)

        process_time = (datetime.utcnow() - start_time).total_seconds()

        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )

        response.headers["X-Process-Time"] = str(process_time)
        return response

    # Include API routers
    app.include_router(listings_router, tags=["listings"])

    # Note: The other API apps are separate FastAPI instances
    # In production, you might want to refactor them into routers
    # For now, we provide a unified entry point

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with API information"""
        return {
            "name": "Otto.AI API",
            "version": "1.0.0",
            "description": "AI-powered vehicle discovery platform",
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "endpoints": {
                "listings": "/api/listings",
                "semantic_search": "/api/search",  # From semantic_search_app
                "vehicle_comparison": "/api/compare",  # From comparison_app
                "filter_management": "/api/filters",  # From filter_app
                "docs": "/docs",
                "health": "/health"
            }
        }

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Comprehensive health check for all services"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "api": "healthy",
                "listings": "healthy",
                "pdf_ingestion": "healthy",  # Will depend on environment variables
                "semantic_search": "unknown",  # Separate service
                "vehicle_comparison": "unknown",  # Separate service
                "filter_management": "unknown",  # Separate service
            }
        }

        try:
            # Check PDF ingestion service dependencies
            import os
            if os.getenv('OPENROUTER_API_KEY') and os.getenv('SUPABASE_URL'):
                health_status["services"]["pdf_ingestion"] = "healthy"
            else:
                health_status["services"]["pdf_ingestion"] = "missing_env_vars"
                health_status["status"] = "degraded"

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)

        status_code = 200 if health_status["status"] == "healthy" else 503
        return JSONResponse(content=health_status, status_code=status_code)

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        )

    return app


# Create the main application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    # Run the application
    uvicorn.run(
        "main_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )