"""
RAGE Task Models — Data structures for background tasks.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a background task."""
    id: int
    command: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    stdout: str = ""
    stderr: str = ""
    returncode: int | None = None
    terminal_name: str = "background"

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    @property
    def duration(self) -> str:
        """Calculate task duration."""
        if not self.started_at:
            return "—"
        start = datetime.fromisoformat(self.started_at)
        end = (
            datetime.fromisoformat(self.completed_at)
            if self.completed_at
            else datetime.now()
        )
        delta = end - start
        total_seconds = int(delta.total_seconds())
        if total_seconds < 60:
            return f"{total_seconds}s"
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}m {seconds}s"

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "id": self.id,
            "command": self.command,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "stdout": self.stdout[-2000:],  # Truncate logs
            "stderr": self.stderr[-2000:],
            "returncode": self.returncode,
            "terminal_name": self.terminal_name,
            "duration": self.duration,
        }
