"""
Background job processing utilities for handling long-running tasks.
Includes task queues, job scheduling, and progress tracking.
"""

import asyncio
import json
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from app.utils.monitoring import performance_metrics, alert_manager


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class JobPriority(Enum):
    """Job priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class JobResult:
    """Result of a background job."""
    job_id: str
    status: JobStatus
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Job:
    """Background job definition."""
    id: str
    task_name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: JobPriority = JobPriority.NORMAL
    max_retries: int = 3
    retry_delay: float = 60.0  # seconds
    timeout: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    status: JobStatus = JobStatus.PENDING
    retries: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class JobQueue:
    """Priority-based job queue with retry logic."""

    def __init__(self, max_concurrent_jobs: int = 5):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.jobs: Dict[str, Job] = {}
        self.priority_queues = {
            JobPriority.CRITICAL: deque(),
            JobPriority.HIGH: deque(),
            JobPriority.NORMAL: deque(),
            JobPriority.LOW: deque()
        }
        self.running_jobs: Dict[str, asyncio.Task] = {}
        self.job_results: Dict[str, JobResult] = {}
        self.job_history = deque(maxlen=1000)
        self.is_processing = False
        self._stop_event = asyncio.Event()

    def add_job(
        self,
        task_name: str,
        func: Callable,
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        retry_delay: float = 60.0,
        timeout: Optional[float] = None,
        scheduled_at: Optional[datetime] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add a job to the queue."""
        job_id = str(uuid.uuid4())

        job = Job(
            id=job_id,
            task_name=task_name,
            func=func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            scheduled_at=scheduled_at,
            metadata=metadata or {}
        )

        self.jobs[job_id] = job

        # Add to appropriate priority queue if not scheduled
        if scheduled_at is None or scheduled_at <= datetime.now():
            self.priority_queues[priority].append(job_id)

        return job_id

    async def start_processing(self):
        """Start processing jobs from the queue."""
        if self.is_processing:
            return

        self.is_processing = True
        self._stop_event.clear()

        while not self._stop_event.is_set():
            try:
                # Process scheduled jobs
                await self._process_scheduled_jobs()

                # Process pending jobs
                await self._process_pending_jobs()

                # Clean up completed tasks
                self._cleanup_completed_tasks()

                # Wait before next iteration
                await asyncio.sleep(1.0)

            except Exception as e:
                await alert_manager.trigger_alert(
                    "job_processor_error",
                    "error",
                    f"Job processor error: {e}"
                )
                await asyncio.sleep(5.0)  # Wait longer on error

    async def stop_processing(self):
        """Stop processing jobs."""
        self.is_processing = False
        self._stop_event.set()

        # Cancel running jobs
        for task in self.running_jobs.values():
            task.cancel()

        # Wait for tasks to complete
        if self.running_jobs:
            await asyncio.gather(*self.running_jobs.values(), return_exceptions=True)

    async def _process_scheduled_jobs(self):
        """Move scheduled jobs to pending queues when ready."""
        current_time = datetime.now()

        scheduled_jobs = [
            job for job in self.jobs.values()
            if job.scheduled_at and job.scheduled_at <= current_time and job.status == JobStatus.PENDING
        ]

        for job in scheduled_jobs:
            self.priority_queues[job.priority].append(job.id)
            job.scheduled_at = None  # Clear schedule

    async def _process_pending_jobs(self):
        """Process jobs from priority queues."""
        if len(self.running_jobs) >= self.max_concurrent_jobs:
            return

        # Process by priority
        for priority in [JobPriority.CRITICAL, JobPriority.HIGH, JobPriority.NORMAL, JobPriority.LOW]:
            queue = self.priority_queues[priority]

            while queue and len(self.running_jobs) < self.max_concurrent_jobs:
                job_id = queue.popleft()

                if job_id in self.jobs:
                    job = self.jobs[job_id]
                    if job.status == JobStatus.PENDING:
                        await self._start_job(job)

    async def _start_job(self, job: Job):
        """Start executing a job."""
        job.status = JobStatus.RUNNING

        # Create and start the task
        task = asyncio.create_task(self._execute_job(job))
        self.running_jobs[job.id] = task

        # Record metrics
        performance_metrics.record_function_call(f"job_started_{job.task_name}", 1)

    async def _execute_job(self, job: Job):
        """Execute a job with error handling and timeout."""
        start_time = time.time()
        result = JobResult(job_id=job.id, status=JobStatus.RUNNING, started_at=datetime.now())

        try:
            # Execute with timeout if specified
            if job.timeout:
                task_result = await asyncio.wait_for(
                    self._run_job_function(job),
                    timeout=job.timeout
                )
            else:
                task_result = await self._run_job_function(job)

            # Job completed successfully
            job.status = JobStatus.COMPLETED
            result.status = JobStatus.COMPLETED
            result.result = task_result
            result.completed_at = datetime.now()
            result.duration = time.time() - start_time

            performance_metrics.record_function_call(f"job_completed_{job.task_name}", result.duration)

        except asyncio.TimeoutError:
            # Job timed out
            job.status = JobStatus.FAILED
            result.status = JobStatus.FAILED
            result.error = f"Job timed out after {job.timeout} seconds"
            result.completed_at = datetime.now()
            result.duration = time.time() - start_time

            await self._handle_job_retry(job)

        except Exception as e:
            # Job failed with exception
            job.status = JobStatus.FAILED
            result.status = JobStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.now()
            result.duration = time.time() - start_time

            await self._handle_job_retry(job)

            performance_metrics.record_function_call(f"job_failed_{job.task_name}", 1)

        finally:
            # Store result and clean up
            self.job_results[job.id] = result
            self.job_history.append({
                'job_id': job.id,
                'task_name': job.task_name,
                'status': result.status.value,
                'duration': result.duration,
                'completed_at': result.completed_at.isoformat() if result.completed_at else None
            })

            if job.id in self.running_jobs:
                del self.running_jobs[job.id]

    async def _run_job_function(self, job: Job):
        """Run the actual job function."""
        if asyncio.iscoroutinefunction(job.func):
            return await job.func(*job.args, **job.kwargs)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: job.func(*job.args, **job.kwargs))

    async def _handle_job_retry(self, job: Job):
        """Handle job retry logic."""
        if job.retries < job.max_retries:
            job.retries += 1
            job.status = JobStatus.RETRY

            # Schedule retry
            retry_time = datetime.now() + timedelta(seconds=job.retry_delay * (2 ** job.retries))  # Exponential backoff
            job.scheduled_at = retry_time

            await alert_manager.trigger_alert(
                "job_retry",
                "warning",
                f"Job {job.task_name} failed, scheduling retry {job.retries}/{job.max_retries}",
                {"job_id": job.id, "retry_time": retry_time.isoformat()}
            )
        else:
            # Max retries exceeded
            await alert_manager.trigger_alert(
                "job_max_retries",
                "error",
                f"Job {job.task_name} failed after {job.max_retries} retries",
                {"job_id": job.id}
            )

    def _cleanup_completed_tasks(self):
        """Clean up completed asyncio tasks."""
        completed_jobs = [
            job_id for job_id, task in self.running_jobs.items()
            if task.done()
        ]

        for job_id in completed_jobs:
            del self.running_jobs[job_id]

    def get_job_status(self, job_id: str) -> Optional[JobResult]:
        """Get the status of a specific job."""
        return self.job_results.get(job_id)

    def get_job_info(self, job_id: str) -> Optional[Job]:
        """Get job information."""
        return self.jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        if job_id in self.running_jobs:
            # Cancel running job
            self.running_jobs[job_id].cancel()
            job = self.jobs.get(job_id)
            if job:
                job.status = JobStatus.CANCELLED
            return True
        elif job_id in self.jobs:
            # Cancel pending job
            job = self.jobs[job_id]
            if job.status == JobStatus.PENDING:
                job.status = JobStatus.CANCELLED

                # Remove from priority queue
                for queue in self.priority_queues.values():
                    if job_id in queue:
                        queue.remove(job_id)
                        break
                return True

        return False

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        pending_counts = {
            priority.name: len(queue)
            for priority, queue in self.priority_queues.items()
        }

        status_counts = defaultdict(int)
        for job in self.jobs.values():
            status_counts[job.status.value] += 1

        return {
            'total_jobs': len(self.jobs),
            'running_jobs': len(self.running_jobs),
            'pending_by_priority': pending_counts,
            'status_distribution': dict(status_counts),
            'max_concurrent_jobs': self.max_concurrent_jobs,
            'is_processing': self.is_processing
        }


class TaskScheduler:
    """Schedule recurring tasks and one-time jobs."""

    def __init__(self, job_queue: JobQueue):
        self.job_queue = job_queue
        self.scheduled_tasks = {}
        self.is_running = False

    def schedule_recurring(
        self,
        name: str,
        func: Callable,
        interval_seconds: float,
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        priority: JobPriority = JobPriority.NORMAL
    ) -> str:
        """Schedule a recurring task."""
        task_id = str(uuid.uuid4())

        self.scheduled_tasks[task_id] = {
            'name': name,
            'func': func,
            'args': args,
            'kwargs': kwargs or {},
            'interval_seconds': interval_seconds,
            'priority': priority,
            'next_run': datetime.now() + timedelta(seconds=interval_seconds),
            'last_run': None,
            'run_count': 0
        }

        return task_id

    async def start_scheduler(self):
        """Start the task scheduler."""
        if self.is_running:
            return

        self.is_running = True

        while self.is_running:
            try:
                current_time = datetime.now()

                for task_id, task_info in self.scheduled_tasks.items():
                    if current_time >= task_info['next_run']:
                        # Schedule the task
                        job_id = self.job_queue.add_job(
                            task_name=f"scheduled_{task_info['name']}",
                            func=task_info['func'],
                            args=task_info['args'],
                            kwargs=task_info['kwargs'],
                            priority=task_info['priority'],
                            metadata={'scheduled_task_id': task_id}
                        )

                        # Update next run time
                        task_info['last_run'] = current_time
                        task_info['next_run'] = current_time + timedelta(seconds=task_info['interval_seconds'])
                        task_info['run_count'] += 1
                        task_info['last_job_id'] = job_id

                await asyncio.sleep(10.0)  # Check every 10 seconds

            except Exception as e:
                await alert_manager.trigger_alert(
                    "scheduler_error",
                    "error",
                    f"Task scheduler error: {e}"
                )
                await asyncio.sleep(30.0)

    def stop_scheduler(self):
        """Stop the task scheduler."""
        self.is_running = False

    def remove_scheduled_task(self, task_id: str) -> bool:
        """Remove a scheduled task."""
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            return True
        return False

    def get_scheduled_tasks(self) -> Dict[str, Any]:
        """Get information about scheduled tasks."""
        return {
            task_id: {
                'name': info['name'],
                'interval_seconds': info['interval_seconds'],
                'next_run': info['next_run'].isoformat(),
                'last_run': info['last_run'].isoformat() if info['last_run'] else None,
                'run_count': info['run_count']
            }
            for task_id, info in self.scheduled_tasks.items()
        }


# Example background tasks
async def generate_story_background(user_id: str, prompt: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Background task for story generation."""
    try:
        # Simulate story generation work
        await asyncio.sleep(5.0)  # Placeholder for actual AI processing

        return {
            'user_id': user_id,
            'story_length': len(prompt) * 10,  # Placeholder
            'generation_time': 5.0,
            'status': 'completed'
        }
    except Exception as e:
        raise Exception(f"Story generation failed: {e}")


async def process_document_background(file_path: str, processing_options: Dict[str, Any]) -> Dict[str, Any]:
    """Background task for document processing."""
    try:
        # Simulate document processing
        await asyncio.sleep(3.0)

        return {
            'file_path': file_path,
            'processed_pages': 10,  # Placeholder
            'processing_time': 3.0,
            'extracted_text_length': 1500,  # Placeholder
            'status': 'completed'
        }
    except Exception as e:
        raise Exception(f"Document processing failed: {e}")


def cleanup_temp_files() -> Dict[str, Any]:
    """Sync task for cleanup operations."""
    import tempfile
    import os

    temp_dir = tempfile.gettempdir()
    cleaned_files = 0

    try:
        # Placeholder cleanup logic
        for filename in os.listdir(temp_dir):
            if filename.startswith('upload_') and filename.endswith('.tmp'):
                file_path = os.path.join(temp_dir, filename)
                if os.path.getmtime(file_path) < time.time() - 3600:  # 1 hour old
                    os.remove(file_path)
                    cleaned_files += 1

        return {
            'cleaned_files': cleaned_files,
            'cleanup_time': time.time()
        }
    except Exception as e:
        raise Exception(f"Cleanup failed: {e}")


# Global instances
job_queue = JobQueue(max_concurrent_jobs=3)
task_scheduler = TaskScheduler(job_queue)

# Schedule recurring cleanup task
task_scheduler.schedule_recurring(
    name="temp_file_cleanup",
    func=cleanup_temp_files,
    interval_seconds=3600.0,  # Every hour
    priority=JobPriority.LOW
)