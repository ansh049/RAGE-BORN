import subprocess
from rage.tools.base import BaseTool, ToolResult

class DockerRunTool(BaseTool):
    """Run a command inside a Docker container."""
    name = "docker_run"
    description = (
        "Execute a command inside a Docker container. "
        "Useful for running isolated code, testing, or building infrastructure."
    )
    parameters = {
        "type": "object",
        "properties": {
            "image": {
                "type": "string",
                "description": "Docker image to use (e.g., 'ubuntu', 'python:3.10-slim')",
            },
            "command": {
                "type": "string",
                "description": "Command to run inside the container",
            },
            "detach": {
                "type": "boolean",
                "description": "Run in background (default: False)",
            }
        },
        "required": ["image", "command"],
    }

    def execute(self, image: str, command: str, detach: bool = False) -> ToolResult:
        try:
            cmd = ["docker", "run", "--rm"]
            if detach:
                cmd.append("-d")
            cmd.extend([image, "sh", "-c", command])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300 if not detach else 30
            )
            
            output = result.stdout + result.stderr
            if result.returncode == 0:
                return ToolResult(success=True, output=f"Docker Command Succeeded:\n{output}")
            else:
                return ToolResult(success=False, output=output, error=f"Docker exited with {result.returncode}")
                
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to run docker: {e}")

class DockerListTool(BaseTool):
    """List running Docker containers."""
    name = "docker_ps"
    description = "List all currently running Docker containers."
    parameters = {
        "type": "object",
        "properties": {},
    }

    def execute(self) -> ToolResult:
        try:
            result = subprocess.run(
                ["docker", "ps", "-a"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return ToolResult(success=True, output=result.stdout)
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to list containers: {e}")
