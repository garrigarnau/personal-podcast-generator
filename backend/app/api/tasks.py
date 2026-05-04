"""
Task management endpoints for monitoring background podcast generation.

This module provides endpoints for:
- Viewing task status and progress
- Listing user tasks
- Cancelling tasks
- Getting task statistics

These endpoints work with the TaskManager to provide visibility into
the async podcast generation pipeline.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.services.task_manager import get_task_manager, TaskManager, TaskInfo, TaskStatus


# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


# ============================================================================
# Response Models
# ============================================================================


class TaskStatusResponse(BaseModel):
    """Response model for task status."""

    task_id: str = Field(..., description="Unique task identifier")
    task_type: str = Field(..., description="Type of task")
    status: str = Field(..., description="Current task status")
    priority: int = Field(..., description="Task priority level")
    podcast_id: Optional[str] = Field(None, description="Associated podcast ID")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    created_at: str = Field(..., description="Task creation timestamp")
    started_at: Optional[str] = Field(None, description="Task start timestamp")
    completed_at: Optional[str] = Field(None, description="Task completion timestamp")
    duration_seconds: Optional[float] = Field(None, description="Task duration in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "task_type": "podcast_generation",
                "status": "completed",
                "priority": 2,
                "podcast_id": "abc-123-def-456",
                "user_id": "user-789",
                "created_at": "2024-05-04T10:00:00",
                "started_at": "2024-05-04T10:00:01",
                "completed_at": "2024-05-04T10:02:30",
                "duration_seconds": 149.5,
                "error_message": None,
                "metadata": {
                    "interests": ["AI", "technology"],
                    "preferences": {"tone": "casual", "length": "medium"}
                }
            }
        }


class TaskListResponse(BaseModel):
    """Response model for list of tasks."""

    tasks: List[TaskStatusResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")

    class Config:
        json_schema_extra = {
            "example": {
                "tasks": [
                    {
                        "task_id": "task-1",
                        "task_type": "podcast_generation",
                        "status": "completed",
                        "priority": 2,
                        "podcast_id": "podcast-1",
                        "user_id": "user-123",
                        "created_at": "2024-05-04T10:00:00",
                        "started_at": "2024-05-04T10:00:01",
                        "completed_at": "2024-05-04T10:02:30",
                        "duration_seconds": 149.5,
                        "error_message": None,
                        "metadata": {}
                    }
                ],
                "total": 1
            }
        }


class TaskStatisticsResponse(BaseModel):
    """Response model for task statistics."""

    total_tasks: int = Field(..., description="Total number of tasks")
    active_tasks: int = Field(..., description="Currently running tasks")
    queue_size: int = Field(..., description="Tasks waiting in queue")
    max_concurrent: int = Field(..., description="Maximum concurrent tasks")
    queued_tasks: int = Field(..., description="Tasks in queued state")
    running_tasks: int = Field(..., description="Tasks in running state")
    completed_tasks: int = Field(..., description="Tasks in completed state")
    failed_tasks: int = Field(..., description="Tasks in failed state")
    cancelled_tasks: int = Field(..., description="Tasks in cancelled state")

    class Config:
        json_schema_extra = {
            "example": {
                "total_tasks": 42,
                "active_tasks": 3,
                "queue_size": 5,
                "max_concurrent": 5,
                "queued_tasks": 5,
                "running_tasks": 3,
                "completed_tasks": 30,
                "failed_tasks": 3,
                "cancelled_tasks": 1
            }
        }


class CancelTaskResponse(BaseModel):
    """Response model for task cancellation."""

    success: bool = Field(..., description="Whether cancellation was successful")
    message: str = Field(..., description="Cancellation result message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Task cancelled successfully"
            }
        }


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get task status",
    description="Retrieve detailed status information for a specific task",
    responses={
        200: {"description": "Task status retrieved successfully"},
        404: {"description": "Task not found"}
    }
)
async def get_task_status(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
) -> TaskStatusResponse:
    """
    Get detailed status of a specific task.

    Args:
        task_id: Unique task identifier
        task_manager: Task manager instance

    Returns:
        TaskStatusResponse with complete task information

    Raises:
        HTTPException: 404 if task not found
    """
    logger.debug(f"Getting status for task: {task_id}")

    task_info = await task_manager.get_task_status(task_id)

    if not task_info:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    return TaskStatusResponse(
        task_id=task_info.task_id,
        task_type=task_info.task_type,
        status=task_info.status.value,
        priority=task_info.priority.value,
        podcast_id=task_info.podcast_id,
        user_id=task_info.user_id,
        created_at=task_info.created_at.isoformat(),
        started_at=task_info.started_at.isoformat() if task_info.started_at else None,
        completed_at=task_info.completed_at.isoformat() if task_info.completed_at else None,
        duration_seconds=task_info.duration_seconds,
        error_message=task_info.error_message,
        metadata=task_info.metadata,
    )


@router.get(
    "/user/{user_id}",
    response_model=TaskListResponse,
    summary="List user tasks",
    description="Get all tasks for a specific user, optionally filtered by status",
    responses={
        200: {"description": "Tasks retrieved successfully"}
    }
)
async def list_user_tasks(
    user_id: str,
    status_filter: Optional[str] = None,
    task_manager: TaskManager = Depends(get_task_manager),
) -> TaskListResponse:
    """
    List all tasks for a specific user.

    Args:
        user_id: User identifier
        status_filter: Optional status filter (queued, running, completed, failed, cancelled)
        task_manager: Task manager instance

    Returns:
        TaskListResponse with list of tasks

    Raises:
        HTTPException: 422 if invalid status filter
    """
    logger.info(f"Listing tasks for user: {user_id}, status_filter: {status_filter}")

    # Validate status filter if provided
    status_enum = None
    if status_filter:
        try:
            status_enum = TaskStatus(status_filter.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status filter: {status_filter}. "
                       f"Valid values: queued, running, completed, failed, cancelled"
            )

    # Get tasks
    tasks = await task_manager.get_user_tasks(
        user_id=user_id,
        status_filter=status_enum
    )

    logger.info(f"Found {len(tasks)} tasks for user {user_id}")

    return TaskListResponse(
        tasks=[
            TaskStatusResponse(
                task_id=task.task_id,
                task_type=task.task_type,
                status=task.status.value,
                priority=task.priority.value,
                podcast_id=task.podcast_id,
                user_id=task.user_id,
                created_at=task.created_at.isoformat(),
                started_at=task.started_at.isoformat() if task.started_at else None,
                completed_at=task.completed_at.isoformat() if task.completed_at else None,
                duration_seconds=task.duration_seconds,
                error_message=task.error_message,
                metadata=task.metadata,
            )
            for task in tasks
        ],
        total=len(tasks)
    )


@router.post(
    "/{task_id}/cancel",
    response_model=CancelTaskResponse,
    summary="Cancel task",
    description="Cancel a running or queued task",
    responses={
        200: {"description": "Task cancellation status"},
        404: {"description": "Task not found"}
    }
)
async def cancel_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
) -> CancelTaskResponse:
    """
    Cancel a task that is running or queued.

    Args:
        task_id: Unique task identifier
        task_manager: Task manager instance

    Returns:
        CancelTaskResponse with cancellation result

    Raises:
        HTTPException: 404 if task not found
    """
    logger.info(f"Attempting to cancel task: {task_id}")

    # Check if task exists
    task_info = await task_manager.get_task_status(task_id)
    if not task_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    # Attempt cancellation
    success = await task_manager.cancel_task(task_id)

    if success:
        message = "Task cancelled successfully"
        logger.info(f"Task {task_id} cancelled")
    else:
        message = "Task could not be cancelled (may already be completed or failed)"
        logger.warning(f"Failed to cancel task {task_id}")

    return CancelTaskResponse(
        success=success,
        message=message
    )


@router.get(
    "/",
    response_model=TaskStatisticsResponse,
    summary="Get task statistics",
    description="Retrieve overall statistics about task execution",
    responses={
        200: {"description": "Statistics retrieved successfully"}
    }
)
async def get_task_statistics(
    task_manager: TaskManager = Depends(get_task_manager),
) -> TaskStatisticsResponse:
    """
    Get overall task manager statistics.

    Args:
        task_manager: Task manager instance

    Returns:
        TaskStatisticsResponse with system statistics
    """
    logger.debug("Fetching task statistics")

    stats = task_manager.get_statistics()

    return TaskStatisticsResponse(**stats)
