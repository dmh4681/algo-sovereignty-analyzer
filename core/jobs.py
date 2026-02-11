"""
Background job system for async wallet analysis.

Provides an in-memory job store for tracking long-running analysis tasks
executed via FastAPI BackgroundTasks.
"""

import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class JobStatus(str, Enum):
    """Job lifecycle states."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    """Represents a background analysis job."""
    id: str
    status: JobStatus
    address: str
    progress_message: str = ""
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize job to dict for API response."""
        return {
            "job_id": self.id,
            "status": self.status.value,
            "address": self.address,
            "progress_message": self.progress_message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class JobStore:
    """Thread-safe in-memory job store with auto-cleanup."""

    MAX_JOBS = 1000
    CLEANUP_AGE_SECONDS = 3600  # 1 hour

    def __init__(self):
        self._jobs: OrderedDict[str, Job] = OrderedDict()
        self._lock = threading.Lock()

    def create_job(self, address: str) -> Job:
        """Create a new queued job."""
        job = Job(
            id=str(uuid.uuid4()),
            status=JobStatus.QUEUED,
            address=address,
        )
        with self._lock:
            self._cleanup_old_jobs()
            self._jobs[job.id] = job
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        with self._lock:
            return self._jobs.get(job_id)

    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        progress_message: Optional[str] = None,
        result: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> Optional[Job]:
        """Update job fields."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None

            now = datetime.now(timezone.utc).isoformat()

            if status is not None:
                job.status = status
                if status == JobStatus.PROCESSING and job.started_at is None:
                    job.started_at = now
                elif status in (JobStatus.COMPLETED, JobStatus.FAILED):
                    job.completed_at = now

            if progress_message is not None:
                job.progress_message = progress_message
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error

            return job

    def _cleanup_old_jobs(self) -> None:
        """Remove completed/failed jobs older than CLEANUP_AGE_SECONDS."""
        now = time.time()
        to_remove = []

        for job_id, job in self._jobs.items():
            if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                if job.completed_at:
                    try:
                        completed = datetime.fromisoformat(job.completed_at).timestamp()
                        if now - completed > self.CLEANUP_AGE_SECONDS:
                            to_remove.append(job_id)
                    except (ValueError, TypeError):
                        to_remove.append(job_id)

        for job_id in to_remove:
            del self._jobs[job_id]

        # Enforce max size by removing oldest
        while len(self._jobs) > self.MAX_JOBS:
            self._jobs.popitem(last=False)


# Singleton
_job_store: Optional[JobStore] = None


def get_job_store() -> JobStore:
    """Get the singleton JobStore instance."""
    global _job_store
    if _job_store is None:
        _job_store = JobStore()
    return _job_store
