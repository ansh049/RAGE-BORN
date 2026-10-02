"""
RAGE BORN History — Persistent task/command history.

Stores every command executed, with timestamps, outputs, duration, and status.
"""

import json
from datetime import datetime
from rage.config import HISTORY_FILE, ensure_rage_dirs


class History:
    """Persistent history of all executed tasks and commands."""

    def __init__(self):
        self._entries: list[dict] = self._load()
        self._next_id = max((e.get("id", 0) for e in self._entries), default=0) + 1

    def _load(self) -> list[dict]:
        """Load history from disk."""
        ensure_rage_dirs()
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save(self):
        """Persist history to disk. Keep last 1000 entries."""
        ensure_rage_dirs()
        self._entries = self._entries[-1000:]
        with open(HISTORY_FILE, "w") as f:
            json.dump(self._entries, f, indent=2)

    def add(self, command: str, output: str, success: bool,
            duration: str = "", error: str = "", tool_name: str = ""):
        """Add a history entry."""
        entry = {
            "id": self._next_id,
            "command": command,
            "output": output[:2000],  # Truncate
            "success": success,
            "duration": duration,
            "error": error[:500],
            "tool_name": tool_name,
            "timestamp": datetime.now().isoformat(),
        }
        self._entries.append(entry)
        self._next_id += 1
        self.save()

    def get_recent(self, count: int = 20) -> list[dict]:
        """Get the most recent history entries."""
        return self._entries[-count:]

    def get_all(self) -> list[dict]:
        """Get all history entries."""
        return list(self._entries)

    def search(self, query: str) -> list[dict]:
        """Search history by command text."""
        query = query.lower()
        return [
            e for e in self._entries
            if query in e.get("command", "").lower()
        ]

    def clear(self):
        """Clear all history."""
        self._entries = []
        self.save()

    def get_stats(self) -> dict:
        """Get history statistics."""
        total = len(self._entries)
        success = sum(1 for e in self._entries if e.get("success"))
        failed = total - success
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": f"{success/total*100:.1f}%" if total > 0 else "N/A",
        }
