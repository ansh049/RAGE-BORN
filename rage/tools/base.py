"""
RAGE BORN Tool Base — Abstract base class for all RAGE tools/plugins.

Every capability in RAGE is implemented as a tool that inherits from BaseTool.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    output: str
    error: str = ""
    data: dict = field(default_factory=dict)

    def __str__(self) -> str:
        if self.success:
            return self.output
        return f"Error: {self.error}\n{self.output}" if self.output else f"Error: {self.error}"


class BaseTool(ABC):
    """Abstract base class for RAGE tools."""

    name: str = "base_tool"
    description: str = "Base tool"
    parameters: dict = {}  # JSON Schema for parameters

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with the given arguments."""
        ...

    def get_schema(self) -> dict:
        """Return the tool schema for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    def validate_args(self, kwargs: dict) -> tuple[bool, str]:
        """Validate arguments against the parameter schema."""
        required = self.parameters.get("required", [])
        properties = self.parameters.get("properties", {})

        for param in required:
            if param not in kwargs:
                return False, f"Missing required parameter: {param}"

        for key in kwargs:
            if key not in properties:
                return False, f"Unknown parameter: {key}"

        return True, ""

class SystemClearContextTool(BaseTool):
    """Clear the LLM conversation history and context."""
    name = "system_clear_context"
    description = (
        "Clear the agent's conversation history. Use this when the user says "
        "'forget everything', 'start over', 'wipe memory', or wants a completely fresh slate."
    )
    parameters = {
        "type": "object",
        "properties": {},
    }

    def execute(self) -> ToolResult:
        # Actual execution is intercepted by agent.py because it needs access to LLMClient
        return ToolResult(success=True, output="Context cleared successfully.")
