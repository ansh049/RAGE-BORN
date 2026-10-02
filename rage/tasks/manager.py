"""
RAGE Background Task Manager.

Runs commands in background threads, tracks progress, captures logs,
provides completion notifications, and supports cancellation.
"""

import subprocess
import threading
import time
from datetime import datetime
from rage.tasks.models import Task, TaskStatus
from rage.config import LOGS_DIR


class TaskManager:
    """Manages background task execution."""

    def __init__(self):
        self._tasks: dict[int, Task] = {}
        self._processes: dict[int, subprocess.Popen] = {}
        self._next_id = 1
        self._lock = threading.Lock()
        self._callbacks: list = []

    def on_complete(self, callback):
        """Register a callback for task completion. callback(task: Task)."""
        self._callbacks.append(callback)

    def submit(self, command: str, terminal_name: str = "background") -> Task:
        """Submit a command for background execution. Returns the task."""
        with self._lock:
            task = Task(
                id=self._next_id,
                command=command,
                terminal_name=terminal_name,
            )
            self._tasks[task.id] = task
            self._next_id += 1

        # Start in background thread
        thread = threading.Thread(
            target=self._run_task,
            args=(task,),
            daemon=True,
        )
        thread.start()

        return task

    def _run_task(self, task: Task):
        """Execute a task in a background thread."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now().isoformat()

        try:
            process = subprocess.Popen(
                task.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            with self._lock:
                self._processes[task.id] = process

            stdout, stderr = process.communicate()

            task.stdout = stdout
            task.stderr = stderr
            task.returncode = process.returncode
            task.completed_at = datetime.now().isoformat()

            if process.returncode == 0:
                task.status = TaskStatus.COMPLETED
            else:
                task.status = TaskStatus.FAILED

        except Exception as e:
            task.stderr = str(e)
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now().isoformat()

        finally:
            with self._lock:
                self._processes.pop(task.id, None)

            # Save log
            self._save_log(task)

            # Fire callbacks
            for cb in self._callbacks:
                try:
                    cb(task)
                except Exception:
                    pass

    def _save_log(self, task: Task):
        """Save task log to file."""
        try:
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            log_file = LOGS_DIR / f"task_{task.id}.log"
            with open(log_file, "w") as f:
                f.write(f"Task #{task.id}\n")
                f.write(f"Command: {task.command}\n")
                f.write(f"Status: {task.status.value}\n")
                f.write(f"Started: {task.started_at}\n")
                f.write(f"Completed: {task.completed_at}\n")
                f.write(f"Duration: {task.duration}\n")
                f.write(f"Return Code: {task.returncode}\n")
                f.write(f"\n{'='*60}\nSTDOUT:\n{'='*60}\n")
                f.write(task.stdout or "(empty)")
                f.write(f"\n{'='*60}\nSTDERR:\n{'='*60}\n")
                f.write(task.stderr or "(empty)")
        except Exception:
            pass

    def get_task(self, task_id: int) -> Task | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def cancel(self, task_id: int) -> bool:
        """Cancel a running task."""
        with self._lock:
            process = self._processes.get(task_id)
            task = self._tasks.get(task_id)

        if process and task:
            try:
                process.terminate()
                time.sleep(0.5)
                if process.poll() is None:
                    process.kill()
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now().isoformat()
                return True
            except Exception:
                return False
        return False

    def list_tasks(self) -> list[dict]:
        """List all tasks as dicts."""
        return [t.to_dict() for t in self._tasks.values()]

    def list_running(self) -> list[dict]:
        """List only running tasks."""
        return [
            t.to_dict() for t in self._tasks.values()
            if t.status == TaskStatus.RUNNING
        ]

    def get_summary(self) -> str:
        """Get a summary of all tasks."""
        total = len(self._tasks)
        running = sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)
        completed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED)

        return (
            f"Tasks: {total} total, {running} running, "
            f"{completed} completed, {failed} failed"
        )
