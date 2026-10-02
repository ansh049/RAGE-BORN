"""
RAGE BORN Memory — Persistent long-term memory.

Stores user preferences, learned facts, project context, and tool-specific
data that persists across sessions.
"""

import json
from datetime import datetime
from rage.config import MEMORY_FILE, ensure_rage_dirs


class Memory:
    """Persistent memory system for RAGE."""

    def __init__(self):
        self._data: dict = self._load()

    def _load(self) -> dict:
        """Load memory from disk."""
        ensure_rage_dirs()
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return self._default()
        return self._default()

    def _default(self) -> dict:
        return {
            "user_preferences": {},
            "facts": [],
            "project_context": {},
            "tool_data": {},
            "updated_at": datetime.now().isoformat(),
        }

    def save(self):
        """Persist memory to disk."""
        ensure_rage_dirs()
        self._data["updated_at"] = datetime.now().isoformat()
        with open(MEMORY_FILE, "w") as f:
            json.dump(self._data, f, indent=2)

    # ── Preferences ───────────────────────────────────────────────────────

    def set_preference(self, key: str, value: str):
        """Set a user preference."""
        self._data["user_preferences"][key] = value
        self.save()

    def get_preference(self, key: str, default: str = "") -> str:
        """Get a user preference."""
        return self._data["user_preferences"].get(key, default)

    def get_all_preferences(self) -> dict:
        """Get all preferences."""
        return dict(self._data["user_preferences"])

    # ── Facts ─────────────────────────────────────────────────────────────

    def remember(self, fact: str):
        """Store a new fact."""
        entry = {
            "fact": fact,
            "timestamp": datetime.now().isoformat(),
        }
        self._data["facts"].append(entry)
        # Keep last 100 facts
        self._data["facts"] = self._data["facts"][-100:]
        self.save()

    def get_facts(self) -> list[str]:
        """Get all remembered facts."""
        return [f["fact"] for f in self._data["facts"]]

    # ── Project Context ───────────────────────────────────────────────────

    def set_project(self, key: str, value):
        """Set project context info."""
        self._data["project_context"][key] = value
        self.save()

    def get_project(self, key: str, default=None):
        """Get project context info."""
        return self._data["project_context"].get(key, default)

    # ── Context for LLM ──────────────────────────────────────────────────

    def get_context_string(self) -> str:
        """Generate a context string for the LLM system prompt."""
        parts = []

        prefs = self.get_all_preferences()
        if prefs:
            parts.append("User Preferences:")
            for k, v in prefs.items():
                parts.append(f"  - {k}: {v}")

        facts = self.get_facts()
        if facts:
            parts.append("\nRemembered Facts:")
            for fact in facts[-20:]:  # Last 20 facts
                parts.append(f"  - {fact}")

        proj = self._data.get("project_context", {})
        if proj:
            parts.append("\nProject Context:")
            for k, v in proj.items():
                parts.append(f"  - {k}: {v}")

        if parts:
            return "\n".join(parts)
        return "No stored memory yet."

    def get_display_info(self) -> str:
        """Get a formatted display of memory for the user."""
        lines = ["📝 RAGE BORN Memory", ""]

        prefs = self.get_all_preferences()
        if prefs:
            lines.append("  [Preferences]")
            for k, v in prefs.items():
                lines.append(f"    {k}: {v}")
            lines.append("")

        facts = self.get_facts()
        if facts:
            lines.append(f"  [Remembered Facts] ({len(facts)} total)")
            for fact in facts[-10:]:
                lines.append(f"    • {fact}")
            lines.append("")

        proj = self._data.get("project_context", {})
        if proj:
            lines.append("  [Project Context]")
            for k, v in proj.items():
                lines.append(f"    {k}: {v}")
            lines.append("")

        if len(lines) <= 2:
            lines.append("  (empty — RAGE BORN will learn as you interact)")

        return "\n".join(lines)
