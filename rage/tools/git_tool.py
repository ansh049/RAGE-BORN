"""
RAGE Git Tool — Git operations wrapper.

Provides common git operations as a single tool with a sub-command pattern.
"""

import os
from rage.tools.base import BaseTool, ToolResult
from rage.tools.terminal import get_session


class GitTool(BaseTool):
    """Execute git operations."""

    name = "git"
    description = (
        "Execute git operations: status, log, diff, add, commit, push, pull, "
        "branch, checkout, clone, and more. Pass any valid git subcommand."
    )
    parameters = {
        "type": "object",
        "properties": {
            "subcommand": {
                "type": "string",
                "description": (
                    "Git subcommand and arguments, e.g. 'status', 'log --oneline -10', "
                    "'commit -m \"feat: add feature\"', 'push origin main'"
                ),
            },
        },
        "required": ["subcommand"],
    }

    def execute(self, subcommand: str) -> ToolResult:
        command = f"git {subcommand}"
        session = get_session("main")
        result = session.run(command, timeout=60)

        output_parts = []
        if result["stdout"]:
            output_parts.append(result["stdout"])
        if result["stderr"]:
            # Git often uses stderr for non-error info (e.g., progress)
            output_parts.append(result["stderr"])

        output = "\n".join(output_parts) if output_parts else "(no output)"

        return ToolResult(
            success=result["success"],
            output=output,
            error=result["stderr"] if not result["success"] else "",
            data={"returncode": result["returncode"]},
        )
