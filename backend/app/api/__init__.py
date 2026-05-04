"""
API endpoints package.

This package contains all FastAPI routers for the Personal Podcast Generator API:
- podcasts: Podcast generation and management endpoints
- users: User management and preferences endpoints
- admin: Admin dashboard and analytics endpoints
- tasks: Background task monitoring and management endpoints
"""

from app.api import podcasts, admin, users, tasks

__all__ = ["podcasts", "admin", "users", "tasks"]
