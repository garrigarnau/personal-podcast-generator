"""
Task Manager for Background Podcast Generation.

This module provides utilities for managing background tasks in the podcast generation
pipeline. It handles task status tracking, error handling, concurrency limits, and
provides a clean interface for integrating with FastAPI's BackgroundTasks.

Key Features:
- Task status tracking and monitoring
- Background task wrapper with comprehensive error handling
- Concurrency limits to prevent resource exhaustion
- Task queuing with priority support
- Graceful shutdown handling
- Metrics and monitoring integration

Architecture:
    FastAPI Endpoint → TaskManager.submit() → Task Queue → Worker Pool → Orchestrator
                           ↓                       ↓              ↓
                    Status Tracking          Priority Queue   Concurrency Limit

Example:
    >>> task_manager = TaskManager(max_concurrent=3)
    >>> task_id = await task_manager.submit_podcast_generation(
    ...     podcast_id="abc-123",
    ...     user_id="user-456",
    ...     interests=["AI", "tech"],
    ...     preferences={"tone": "casual"}
    ... )
    >>> status = await task_manager.get_task_status(task_id)
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from uuid import uuid4
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.services.orchestrator import trigger_podcast_generation


# Configure logging
logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    """Task priority levels (lower number = higher priority)."""

    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class TaskInfo:
    """
    Information about a background task.

    Attributes:
        task_id: Unique task identifier
        task_type: Type of task (e.g., "podcast_generation")
        status: Current task status
        priority: Task priority level
        podcast_id: Associated podcast ID (if applicable)
        user_id: Associated user ID
        created_at: Task creation timestamp
        started_at: Task start timestamp
        completed_at: Task completion timestamp
        error_message: Error details if task failed
        metadata: Additional task metadata
        result: Task result data
    """

    task_id: str
    task_type: str
    status: TaskStatus
    priority: TaskPriority = TaskPriority.NORMAL
    podcast_id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert TaskInfo to dictionary."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "priority": self.priority.value,
            "podcast_id": self.podcast_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "result": self.result,
        }

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate task duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state (completed, failed, or cancelled)."""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]


class TaskManager:
    """
    Manager for background task execution and monitoring.

    This class provides a centralized system for managing background tasks
    with support for concurrency limits, task queuing, status tracking,
    and comprehensive error handling.

    Features:
    - Concurrent task execution with configurable limits
    - Task priority queue
    - Status tracking and monitoring
    - Graceful error handling
    - Metrics collection
    - Clean shutdown handling

    Example:
        >>> # Initialize task manager
        >>> task_manager = TaskManager(
        ...     max_concurrent=3,
        ...     enable_queue=True
        ... )
        >>>
        >>> # Submit a task
        >>> task_id = await task_manager.submit_podcast_generation(
        ...     podcast_id="abc-123",
        ...     user_id="user-456",
        ...     interests=["AI", "technology"],
        ...     preferences={"tone": "casual", "length": "medium"},
        ...     priority=TaskPriority.HIGH
        ... )
        >>>
        >>> # Check task status
        >>> status = await task_manager.get_task_status(task_id)
        >>> print(f"Task {task_id}: {status.status.value}")
        >>>
        >>> # Get all tasks for a user
        >>> user_tasks = await task_manager.get_user_tasks(user_id="user-456")
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        enable_queue: bool = True,
        queue_max_size: int = 100,
    ):
        """
        Initialize TaskManager.

        Args:
            max_concurrent: Maximum number of concurrent tasks
            enable_queue: Whether to enable task queuing
            queue_max_size: Maximum queue size (0 = unlimited)
        """
        self.max_concurrent = max_concurrent
        self.enable_queue = enable_queue
        self.queue_max_size = queue_max_size

        # Task tracking
        self._tasks: Dict[str, TaskInfo] = {}
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(
            maxsize=queue_max_size if queue_max_size > 0 else 0
        )

        # Concurrency control
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._shutdown = False

        # Start queue worker if queuing is enabled
        self._worker_task: Optional[asyncio.Task] = None
        if enable_queue:
            self._worker_task = asyncio.create_task(self._queue_worker())

        logger.info(
            f"TaskManager initialized: max_concurrent={max_concurrent}, "
            f"enable_queue={enable_queue}, queue_max_size={queue_max_size}"
        )

    async def submit_podcast_generation(
        self,
        podcast_id: str,
        user_id: str,
        interests: List[str],
        preferences: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        """
        Submit a podcast generation task.

        Args:
            podcast_id: UUID of podcast to generate
            user_id: UUID of user requesting generation
            interests: List of user interests
            preferences: Generation preferences
            priority: Task priority level

        Returns:
            Task ID for tracking

        Raises:
            RuntimeError: If task manager is shutting down
            asyncio.QueueFull: If queue is full and queuing is enabled

        Example:
            >>> task_id = await task_manager.submit_podcast_generation(
            ...     podcast_id="550e8400-e29b-41d4-a716-446655440000",
            ...     user_id="user-123",
            ...     interests=["AI", "technology", "startups"],
            ...     preferences={
            ...         "tone": "casual",
            ...         "length": "medium",
            ...         "max_articles": 5
            ...     },
            ...     priority=TaskPriority.HIGH
            ... )
        """
        if self._shutdown:
            raise RuntimeError("TaskManager is shutting down, cannot accept new tasks")

        task_id = str(uuid4())

        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            task_type="podcast_generation",
            status=TaskStatus.QUEUED,
            priority=priority,
            podcast_id=podcast_id,
            user_id=user_id,
            metadata={
                "interests": interests,
                "preferences": preferences,
            },
        )

        self._tasks[task_id] = task_info

        logger.info(
            f"Task submitted: task_id={task_id}, podcast_id={podcast_id}, "
            f"priority={priority.name}"
        )

        # Add to queue if enabled, otherwise run directly
        if self.enable_queue:
            await self._task_queue.put((priority.value, task_id, podcast_id, user_id, interests, preferences))
            logger.debug(f"Task {task_id} added to queue")
        else:
            # Run directly with concurrency limit
            asyncio.create_task(
                self._run_task_with_limit(
                    task_id=task_id,
                    podcast_id=podcast_id,
                    user_id=user_id,
                    interests=interests,
                    preferences=preferences,
                )
            )

        return task_id

    async def _queue_worker(self) -> None:
        """
        Background worker that processes tasks from the queue.

        This worker continuously polls the task queue and executes tasks
        respecting the concurrency limit.
        """
        logger.info("Task queue worker started")

        while not self._shutdown:
            try:
                # Get next task from queue (blocks until available)
                priority, task_id, podcast_id, user_id, interests, preferences = (
                    await asyncio.wait_for(self._task_queue.get(), timeout=1.0)
                )

                logger.debug(f"Worker picked up task {task_id} from queue")

                # Run task with concurrency limit
                asyncio.create_task(
                    self._run_task_with_limit(
                        task_id=task_id,
                        podcast_id=podcast_id,
                        user_id=user_id,
                        interests=interests,
                        preferences=preferences,
                    )
                )

                self._task_queue.task_done()

            except asyncio.TimeoutError:
                # No tasks in queue, continue polling
                continue
            except Exception as e:
                logger.error(f"Queue worker error: {e}", exc_info=True)
                await asyncio.sleep(1.0)

        logger.info("Task queue worker stopped")

    async def _run_task_with_limit(
        self,
        task_id: str,
        podcast_id: str,
        user_id: str,
        interests: List[str],
        preferences: Dict[str, Any],
    ) -> None:
        """
        Run a task with concurrency limit enforcement.

        Args:
            task_id: Task identifier
            podcast_id: Podcast ID
            user_id: User ID
            interests: User interests
            preferences: Generation preferences
        """
        async with self._semaphore:
            await self._execute_podcast_generation(
                task_id=task_id,
                podcast_id=podcast_id,
                user_id=user_id,
                interests=interests,
                preferences=preferences,
            )

    async def _execute_podcast_generation(
        self,
        task_id: str,
        podcast_id: str,
        user_id: str,
        interests: List[str],
        preferences: Dict[str, Any],
    ) -> None:
        """
        Execute podcast generation task with comprehensive error handling.

        Args:
            task_id: Task identifier
            podcast_id: Podcast ID
            user_id: User ID
            interests: User interests
            preferences: Generation preferences
        """
        task_info = self._tasks.get(task_id)
        if not task_info:
            logger.error(f"Task {task_id} not found in task registry")
            return

        try:
            # Update status to running
            task_info.status = TaskStatus.RUNNING
            task_info.started_at = datetime.utcnow()
            logger.info(f"Task {task_id} started execution")

            # Create database session for this task
            async with async_session_factory() as db:
                # Execute podcast generation
                await trigger_podcast_generation(
                    podcast_id=podcast_id,
                    user_id=user_id,
                    interests=interests,
                    preferences=preferences,
                    db=db,
                )

            # Mark as completed
            task_info.status = TaskStatus.COMPLETED
            task_info.completed_at = datetime.utcnow()
            task_info.result = {"podcast_id": podcast_id, "status": "completed"}

            logger.info(
                f"Task {task_id} completed successfully in "
                f"{task_info.duration_seconds:.2f}s"
            )

        except asyncio.CancelledError:
            # Task was cancelled
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = datetime.utcnow()
            task_info.error_message = "Task was cancelled"
            logger.warning(f"Task {task_id} was cancelled")
            raise

        except Exception as e:
            # Task failed
            task_info.status = TaskStatus.FAILED
            task_info.completed_at = datetime.utcnow()
            task_info.error_message = str(e)
            logger.error(
                f"Task {task_id} failed: {e}",
                exc_info=True,
            )

        finally:
            # Cleanup
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]

    async def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """
        Get status of a specific task.

        Args:
            task_id: Task identifier

        Returns:
            TaskInfo if task exists, None otherwise

        Example:
            >>> task_info = await task_manager.get_task_status("task-123")
            >>> if task_info:
            ...     print(f"Status: {task_info.status.value}")
            ...     if task_info.is_terminal:
            ...         print(f"Duration: {task_info.duration_seconds}s")
        """
        return self._tasks.get(task_id)

    async def get_user_tasks(
        self,
        user_id: str,
        status_filter: Optional[TaskStatus] = None,
    ) -> List[TaskInfo]:
        """
        Get all tasks for a specific user.

        Args:
            user_id: User identifier
            status_filter: Optional status filter

        Returns:
            List of TaskInfo objects for the user

        Example:
            >>> # Get all tasks for user
            >>> tasks = await task_manager.get_user_tasks("user-123")
            >>>
            >>> # Get only running tasks
            >>> running_tasks = await task_manager.get_user_tasks(
            ...     "user-123",
            ...     status_filter=TaskStatus.RUNNING
            ... )
        """
        user_tasks = [
            task for task in self._tasks.values()
            if task.user_id == user_id
        ]

        if status_filter:
            user_tasks = [
                task for task in user_tasks
                if task.status == status_filter
            ]

        return sorted(user_tasks, key=lambda t: t.created_at, reverse=True)

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running or queued task.

        Args:
            task_id: Task identifier

        Returns:
            True if task was cancelled, False otherwise

        Example:
            >>> success = await task_manager.cancel_task("task-123")
            >>> if success:
            ...     print("Task cancelled successfully")
        """
        task_info = self._tasks.get(task_id)
        if not task_info:
            logger.warning(f"Cannot cancel task {task_id}: not found")
            return False

        if task_info.is_terminal:
            logger.warning(f"Cannot cancel task {task_id}: already in terminal state")
            return False

        # Cancel active task if running
        if task_id in self._active_tasks:
            self._active_tasks[task_id].cancel()
            logger.info(f"Cancelled running task {task_id}")
            return True

        # Mark queued task as cancelled
        task_info.status = TaskStatus.CANCELLED
        task_info.completed_at = datetime.utcnow()
        task_info.error_message = "Cancelled by user"
        logger.info(f"Cancelled queued task {task_id}")
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get task manager statistics.

        Returns:
            Dictionary with statistics about tasks and system state

        Example:
            >>> stats = task_manager.get_statistics()
            >>> print(f"Active tasks: {stats['active_tasks']}")
            >>> print(f"Queue size: {stats['queue_size']}")
            >>> print(f"Total completed: {stats['completed_tasks']}")
        """
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = sum(
                1 for task in self._tasks.values() if task.status == status
            )

        return {
            "total_tasks": len(self._tasks),
            "active_tasks": len(self._active_tasks),
            "queue_size": self._task_queue.qsize() if self.enable_queue else 0,
            "max_concurrent": self.max_concurrent,
            "status_counts": status_counts,
            "queued_tasks": status_counts.get(TaskStatus.QUEUED.value, 0),
            "running_tasks": status_counts.get(TaskStatus.RUNNING.value, 0),
            "completed_tasks": status_counts.get(TaskStatus.COMPLETED.value, 0),
            "failed_tasks": status_counts.get(TaskStatus.FAILED.value, 0),
            "cancelled_tasks": status_counts.get(TaskStatus.CANCELLED.value, 0),
        }

    async def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """
        Cleanup old completed/failed tasks from memory.

        Args:
            max_age_hours: Maximum age of tasks to keep (in hours)

        Returns:
            Number of tasks cleaned up

        Example:
            >>> # Remove tasks older than 24 hours
            >>> count = await task_manager.cleanup_old_tasks(max_age_hours=24)
            >>> print(f"Cleaned up {count} old tasks")
        """
        cutoff_time = datetime.utcnow()
        cutoff_time = cutoff_time.replace(hour=cutoff_time.hour - max_age_hours)

        tasks_to_remove = [
            task_id
            for task_id, task_info in self._tasks.items()
            if task_info.is_terminal
            and task_info.completed_at
            and task_info.completed_at < cutoff_time
        ]

        for task_id in tasks_to_remove:
            del self._tasks[task_id]

        if tasks_to_remove:
            logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")

        return len(tasks_to_remove)

    async def shutdown(self, timeout: float = 30.0) -> None:
        """
        Gracefully shutdown the task manager.

        Waits for active tasks to complete and stops accepting new tasks.

        Args:
            timeout: Maximum time to wait for tasks to complete (seconds)

        Example:
            >>> # Shutdown on application exit
            >>> await task_manager.shutdown(timeout=60.0)
        """
        logger.info(f"TaskManager shutdown initiated (timeout={timeout}s)")
        self._shutdown = True

        # Stop queue worker
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        # Wait for active tasks to complete
        if self._active_tasks:
            logger.info(f"Waiting for {len(self._active_tasks)} active tasks to complete...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._active_tasks.values(), return_exceptions=True),
                    timeout=timeout,
                )
                logger.info("All active tasks completed")
            except asyncio.TimeoutError:
                logger.warning(
                    f"Shutdown timeout reached, cancelling {len(self._active_tasks)} remaining tasks"
                )
                for task in self._active_tasks.values():
                    task.cancel()

        logger.info("TaskManager shutdown complete")


# ============================================================================
# Singleton Instance
# ============================================================================

_task_manager_instance: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """
    Get or create singleton TaskManager instance.

    Returns:
        TaskManager instance

    Example:
        >>> from app.services.task_manager import get_task_manager
        >>>
        >>> task_manager = get_task_manager()
        >>> task_id = await task_manager.submit_podcast_generation(...)
    """
    global _task_manager_instance

    if _task_manager_instance is None:
        _task_manager_instance = TaskManager(
            max_concurrent=5,
            enable_queue=True,
            queue_max_size=100,
        )
        logger.info("Created new TaskManager singleton instance")

    return _task_manager_instance


# ============================================================================
# Background Task Wrapper
# ============================================================================


async def run_background_task(
    task_func: Callable,
    *args,
    task_name: str = "background_task",
    **kwargs,
) -> None:
    """
    Wrapper for running background tasks with error handling.

    This is a utility function for running arbitrary async functions as
    background tasks with comprehensive error handling and logging.

    Args:
        task_func: Async function to run
        *args: Positional arguments for task_func
        task_name: Name for logging purposes
        **kwargs: Keyword arguments for task_func

    Example:
        >>> async def my_task(param1, param2):
        ...     # Do something async
        ...     await some_operation(param1, param2)
        >>>
        >>> # Run as background task
        >>> background_tasks.add_task(
        ...     run_background_task,
        ...     my_task,
        ...     "value1",
        ...     "value2",
        ...     task_name="my_custom_task"
        ... )
    """
    logger.info(f"Background task '{task_name}' started")
    start_time = datetime.utcnow()

    try:
        await task_func(*args, **kwargs)

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Background task '{task_name}' completed successfully in {duration:.2f}s"
        )

    except asyncio.CancelledError:
        logger.warning(f"Background task '{task_name}' was cancelled")
        raise

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            f"Background task '{task_name}' failed after {duration:.2f}s: {e}",
            exc_info=True,
        )
        # Don't re-raise - background tasks should not crash the application
