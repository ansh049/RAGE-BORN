"""
RAGE Terminal Tool — Shell command execution and multi-tab sessions.

Executes commands via subprocess with safety checks, output capture,
and support for named terminal sessions (tabs).
"""

import subprocess
import shlex
import os
import time
from rage.tools.base import BaseTool, ToolResult
from rage.safety import SafetyChecker


# ── Terminal Session Manager ──────────────────────────────────────────────────

class TerminalSession:
    """Represents a named terminal tab/session."""

    def __init__(self, name: str, cwd: str | None = None):
        self.name = name
        self.cwd = cwd or os.getcwd()
        self.history: list[dict] = []
        self.env: dict = dict(os.environ)
        self.active_process = None
        self.active_log_path = None

    def run(self, command: str, timeout: int = 120, external_window: bool = False, background: bool = False) -> dict:
        """Execute a command in this session's context."""
        start = time.time()
        try:
            if background or external_window:
                import shutil
                import tempfile
                
                # Keep the same log file for the session so it can be monitored continuously
                if not self.active_log_path or not os.path.exists(self.active_log_path):
                    fd, self.active_log_path = tempfile.mkstemp(suffix=".log")
                    os.close(fd)
                else:
                    open(self.active_log_path, 'w').close() # Clear previous logs

                if external_window:
                    terminals = ["kitty", "gnome-terminal", "alacritty", "konsole", "xterm"]
                    term_exe = next((t for t in terminals if shutil.which(t)), None)
                    
                    if term_exe:
                        wrapper = "eval \"$1\" 2>&1 | tee \"$2\"; echo; read -p 'Press Enter to close...'"
                        if term_exe == "gnome-terminal":
                            term_cmd = [term_exe, "--", "bash", "-c", wrapper, "--", command, self.active_log_path]
                        else:
                            term_cmd = [term_exe, "-e", "bash", "-c", wrapper, "--", command, self.active_log_path]
                            
                        if background:
                            self.active_process = subprocess.Popen(term_cmd, cwd=self.cwd, env=self.env)
                            return {
                                "command": command,
                                "stdout": f"Command started in background external window. Use read_terminal to view logs.",
                                "stderr": "",
                                "returncode": 0,
                                "duration": "0.0s",
                                "success": True,
                            }
                        else:
                            proc = subprocess.run(term_cmd, cwd=self.cwd, env=self.env)
                            with open(self.active_log_path, "r", encoding="utf-8", errors="replace") as f:
                                stdout = f.read()
                            duration = time.time() - start
                            entry = {
                                "command": command,
                                "stdout": stdout,
                                "stderr": "",
                                "returncode": proc.returncode,
                                "duration": f"{duration:.2f}s",
                                "success": proc.returncode == 0,
                            }
                            self.history.append(entry)
                            self._update_cwd(command)
                            return entry
                
                if background:
                    # Non-visual background execution
                    log_file = open(self.active_log_path, 'w')
                    self.active_process = subprocess.Popen(
                        command,
                        shell=True,
                        cwd=self.cwd,
                        env=self.env,
                        stdout=log_file,
                        stderr=subprocess.STDOUT
                    )
                    return {
                        "command": command,
                        "stdout": f"Command started in background. Use read_terminal to view logs.",
                        "stderr": "",
                        "returncode": 0,
                        "duration": "0.0s",
                        "success": True,
                    }

            # Normal blocking execution (fallback or default)
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.cwd,
                env=self.env,
                timeout=timeout,
            )
            duration = time.time() - start
            entry = {
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "duration": f"{duration:.2f}s",
                "success": result.returncode == 0,
            }
            self.history.append(entry)
            self._update_cwd(command)
            return entry

        except subprocess.TimeoutExpired:
            duration = time.time() - start
            entry = {
                "command": command,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "returncode": -1,
                "duration": f"{duration:.2f}s",
                "success": False,
            }
            self.history.append(entry)
            return entry

        except Exception as e:
            duration = time.time() - start
            entry = {
                "command": command,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "duration": f"{duration:.2f}s",
                "success": False,
            }
            self.history.append(entry)
            return entry

    def _update_cwd(self, command: str):
        if command.strip().startswith("cd "):
            try:
                target = command.strip()[3:].strip().strip("'\"")
                new_cwd = os.path.normpath(os.path.join(self.cwd, target))
                if os.path.isdir(new_cwd):
                    self.cwd = new_cwd
            except Exception:
                pass


# Global terminal sessions
_sessions: dict[str, TerminalSession] = {}


def get_session(name: str = "main") -> TerminalSession:
    """Get or create a terminal session by name."""
    if name not in _sessions:
        _sessions[name] = TerminalSession(name)
    return _sessions[name]


def list_sessions() -> list[dict]:
    """List all active terminal sessions."""
    return [
        {
            "name": s.name,
            "cwd": s.cwd,
            "commands_run": len(s.history),
        }
        for s in _sessions.values()
    ]


# ── Tools ─────────────────────────────────────────────────────────────────────

class RunCommandTool(BaseTool):
    """Execute shell commands."""

    name = "run_command"
    description = (
        "Execute a shell command in a terminal session. "
        "Use this for any system operation: installing packages, running scripts, "
        "file operations, git commands, docker, and more. "
        "Specify a terminal_name to use a specific session (defaults to 'main')."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute",
            },
            "terminal_name": {
                "type": "string",
                "description": "Name of the terminal session/tab to use (default: 'main')",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default: 120)",
            },
            "external_window": {
                "type": "boolean",
                "description": "If true, opens the command in a new external terminal window so the user can interact and see it running. The output is still captured.",
            },
            "background": {
                "type": "boolean",
                "description": "If true, runs the command asynchronously in the background. Use read_terminal to fetch its output later.",
            },
        },
        "required": ["command"],
    }

    def __init__(self):
        self.safety = SafetyChecker()

    def execute(self, command: str, terminal_name: str = "main",
                timeout: int = 120, external_window: bool = False, background: bool = False) -> ToolResult:
        """Execute a shell command with safety checks."""

        # Safety check
        danger = self.safety.check_command(command)
        if danger:
            approval = self.safety.request_approval(danger)
            if approval == "n":
                return ToolResult(
                    success=False,
                    output="",
                    error="Command blocked by safety system. User denied execution.",
                )

        # Execute
        session = get_session(terminal_name)
        result = session.run(command, timeout=timeout, external_window=external_window, background=background)

        output_parts = []
        if result["stdout"]:
            output_parts.append(result["stdout"])
        if result["stderr"]:
            output_parts.append(f"[stderr] {result['stderr']}")

        output = "\n".join(output_parts) if output_parts else "(no output)"

        return ToolResult(
            success=result["success"],
            output=output,
            error=result["stderr"] if not result["success"] else "",
            data={
                "returncode": result["returncode"],
                "duration": result["duration"],
                "terminal": terminal_name,
            },
        )


class ListTerminalsTool(BaseTool):
    """List active terminal sessions."""

    name = "list_terminals"
    description = "List all active terminal sessions/tabs with their working directories."
    parameters = {
        "type": "object",
        "properties": {},
    }

    def execute(self) -> ToolResult:
        sessions = list_sessions()
        if not sessions:
            return ToolResult(success=True, output="No active terminal sessions.")

        lines = ["Active Terminal Sessions:", ""]
        for s in sessions:
            lines.append(f"  📟 {s['name']}  —  {s['cwd']}  ({s['commands_run']} commands)")

        return ToolResult(success=True, output="\n".join(lines))


class SystemScreenshotTool(BaseTool):
    """Take a screenshot of the current OS screen."""

    name = "system_screenshot"
    description = (
        "Take a screenshot of the entire OS desktop/screen. "
        "Useful to see what is currently visible outside of the browser, "
        "like desktop windows, terminal, or system dialogs. "
        "Returns the path to the saved screenshot image."
    )
    parameters = {
        "type": "object",
        "properties": {},
    }

    def execute(self) -> ToolResult:
        try:
            from PIL import ImageGrab
            import tempfile
            import os
            
            # Take a screenshot
            img = ImageGrab.grab()
            
            # Save to temporary file
            fd, path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            
            img.save(path)
            
            return ToolResult(
                success=True,
                output=f"Screenshot successfully captured and saved to: {path}\nResolution: {img.size[0]}x{img.size[1]}",
                data={"path": path, "width": img.size[0], "height": img.size[1]}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to take screenshot: {str(e)}"
            )


class ReadTerminalTool(BaseTool):
    """Read logs from an active background terminal session."""

    name = "read_terminal"
    description = (
        "Read the last N lines of output from a terminal session, especially useful "
        "for monitoring long-running background tasks (like dev servers)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "terminal_name": {
                "type": "string",
                "description": "Name of the terminal session (default: 'main')",
            },
            "lines": {
                "type": "integer",
                "description": "Number of lines to read from the end (default: 100)",
            }
        }
    }

    def execute(self, terminal_name: str = "main", lines: int = 100) -> ToolResult:
        session = get_session(terminal_name)
        if not session.active_log_path or not os.path.exists(session.active_log_path):
            return ToolResult(
                success=False,
                output="",
                error=f"No active background log found for terminal '{terminal_name}'."
            )
            
        try:
            # Check process status
            status = "RUNNING"
            if session.active_process:
                if session.active_process.poll() is not None:
                    status = f"FINISHED (exit code {session.active_process.returncode})"
                    
            with open(session.active_log_path, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
                
            tail = "".join(all_lines[-lines:]) if all_lines else "(no output yet)"
            
            output = f"Terminal '{terminal_name}' Status: {status}\n\n[Last {lines} lines]\n{tail}"
            return ToolResult(success=True, output=output)
            
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Error reading log: {e}")
