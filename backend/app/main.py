"""
Personal Podcast Generator API - Main Application

This module sets up the FastAPI application with:
- CORS middleware for frontend communication
- Router registration for all endpoints
- Lifecycle events for database initialization
- Global error handlers
- Comprehensive logging
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import init_db, close_db
from app.api import podcasts, admin, users, tasks, auth
from app.services.task_manager import get_task_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for database connections,
    task manager initialization, and other resources.
    """
    # Startup
    logger.info("Starting up Personal Podcast Generator API...")

    try:
        # Note: Database tables are created via Alembic migrations
        # Run 'alembic upgrade head' before starting the server
        # await init_db()  # Only needed for fresh setup without migrations
        logger.info("Database connection pool ready")

        # Initialize task manager (singleton will be created on first access)
        task_manager = get_task_manager()
        logger.info("Task manager initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
        raise

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Personal Podcast Generator API...")

    try:
        # Shutdown task manager gracefully
        task_manager = get_task_manager()
        await task_manager.shutdown(timeout=60.0)
        logger.info("Task manager shutdown complete")

        # Close database connections
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)

    logger.info("Application shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title="Personal Podcast Generator API",
    description=(
        "Production-grade API for generating personalized podcasts from web content. "
        "Features include async generation, status polling, user management, and "
        "comprehensive admin analytics."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend dev server (Vite)
        "http://localhost:3000",  # Frontend production/Docker
        "http://127.0.0.1:5173",  # Localhost alternative
        "http://127.0.0.1:3000",  # Localhost alternative
        "http://frontend",        # Docker container name
        "http://frontend:80",     # Docker container with port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors with detailed error messages.
    """
    logger.warning(
        f"Validation error for {request.method} {request.url.path}: {exc.errors()}"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed",
            "errors": exc.errors(),
        }
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handle database errors gracefully.
    """
    logger.error(
        f"Database error for {request.method} {request.url.path}: {str(exc)}",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "A database error occurred. Please try again later.",
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Catch-all handler for unexpected errors.
    """
    logger.error(
        f"Unexpected error for {request.method} {request.url.path}: {str(exc)}",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
        }
    )


# Register routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(podcasts.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")

logger.info("API routers registered successfully")


# Health check and root endpoints
@app.get(
    "/",
    tags=["root"],
    summary="Root endpoint",
    description="Returns basic API information and status"
)
async def root():
    """
    Root endpoint providing API information.
    """
    return {
        "name": "Personal Podcast Generator API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Check if the API is running and healthy"
)
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    return {
        "status": "healthy",
        "service": "personal-podcast-generator",
        "version": "1.0.0",
    }
