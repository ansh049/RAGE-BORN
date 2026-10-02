"""
RAGE BORN Tool Registry — Discovers, registers, and manages tools.

Provides the combined tool schema that gets injected into the LLM system prompt.
"""

from rage.tools.base import BaseTool, SystemClearContextTool


class ToolRegistry:
    """Registry for managing RAGE tools."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """Register a tool instance."""
        self._tools[tool.name] = tool

    def unregister(self, name: str):
        """Unregister a tool by name."""
        self._tools.pop(name, None)

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[BaseTool]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_schemas(self) -> list[dict]:
        """Get schemas for all registered tools."""
        return [tool.get_schema() for tool in self._tools.values()]

    def get_tools_description(self) -> str:
        """Generate a human-readable description of all tools for the LLM."""
        lines = []
        for tool in self._tools.values():
            lines.append(f"### {tool.name}")
            lines.append(f"{tool.description}")
            if tool.parameters.get("properties"):
                lines.append("Parameters:")
                for param, info in tool.parameters["properties"].items():
                    required = param in tool.parameters.get("required", [])
                    req_label = " (required)" if required else " (optional)"
                    lines.append(
                        f"  - {param}{req_label}: {info.get('description', info.get('type', 'any'))}"
                    )
            lines.append("")
        return "\n".join(lines)

    def execute(self, tool_name: str, args: dict):
        """Execute a tool by name with the given arguments."""
        tool = self.get(tool_name)
        if not tool:
            from rage.tools.base import ToolResult
            return ToolResult(
                success=False,
                output="",
                error=f"Unknown tool: {tool_name}. Available tools: {', '.join(self._tools.keys())}",
            )

        valid, err = tool.validate_args(args)
        if not valid:
            from rage.tools.base import ToolResult
            return ToolResult(success=False, output="", error=err)

        return tool.execute(**args)


def create_default_registry() -> ToolRegistry:
    """Create a registry with all default tools."""
    from rage.tools.terminal import RunCommandTool, ListTerminalsTool, SystemScreenshotTool, ReadTerminalTool
    from rage.tools.filesystem import (
        ReadFileTool,
        WriteFileTool,
        ListDirectoryTool,
        SearchFilesTool,
    )
    from rage.tools.git_tool import GitTool
    from rage.tools.browser import (
        BrowserOpenTool,
        BrowserClickTool,
        BrowserTypeTool,
        BrowserReadTool,
        BrowserScreenshotTool,
        BrowserVisionTool,
        BrowserScrollTool,
        BrowserSearchTool,
        BrowserTabsTool,
        BrowserKeyTool,
        BrowserCloseTool,
        BrowserLinksTool,
        BrowserJSTool,
        BrowserWaitTool,
        BrowserElementsTool,
    )
    from rage.tools.google_workspace import (
        GWorkspaceDocsTool,
        GWorkspaceSheetsTool,
        GWorkspaceGmailTool,
        GWorkspaceMeetTool,
        GWorkspaceCalendarTool,
    )
    from rage.tools.docker_tool import DockerRunTool, DockerListTool
    from rage.tools.image_gen import GenerateImageTool

    registry = ToolRegistry()

    # Terminal tools
    registry.register(RunCommandTool())
    registry.register(ListTerminalsTool())
    registry.register(ReadTerminalTool())

    # System tools
    registry.register(SystemClearContextTool())
    registry.register(SystemScreenshotTool())
    registry.register(GenerateImageTool())

    # File system tools
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(ListDirectoryTool())
    registry.register(SearchFilesTool())

    # Git tools
    registry.register(GitTool())

    # Browser tools
    registry.register(BrowserOpenTool())
    registry.register(BrowserClickTool())
    registry.register(BrowserTypeTool())
    registry.register(BrowserReadTool())
    registry.register(BrowserScreenshotTool())
    registry.register(BrowserVisionTool())
    registry.register(BrowserScrollTool())
    registry.register(BrowserSearchTool())
    registry.register(BrowserTabsTool())
    registry.register(BrowserKeyTool())
    registry.register(BrowserCloseTool())
    registry.register(BrowserLinksTool())
    registry.register(BrowserElementsTool())
    registry.register(BrowserJSTool())
    registry.register(BrowserWaitTool())

    # Load user plugins from ~/.rage/plugins/
    from rage.tools.plugin import load_plugins
    load_plugins(registry)

    # Google Workspace tools
    registry.register(GWorkspaceDocsTool())
    registry.register(GWorkspaceSheetsTool())
    registry.register(GWorkspaceGmailTool())
    registry.register(GWorkspaceMeetTool())
    registry.register(GWorkspaceCalendarTool())
    
    # Docker tools
    registry.register(DockerRunTool())
    registry.register(DockerListTool())
    
    # OS Tools
    from rage.tools.os_tools import OpenAppTool, KeyboardPressTool, KeyboardTypeTool
    registry.register(OpenAppTool())
    registry.register(KeyboardPressTool())
    registry.register(KeyboardTypeTool())

    return registry

