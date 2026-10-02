"""
RAGE BORN UI — Rich Terminal Rendering.

Provides markdown rendering, streaming output, panels, progress bars,
and all visual components for the terminal interface.
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
import sys
import time


# ── Theme Colors ──────────────────────────────────────────────────────────────
COLORS = {
    "primary": "#FF3D00",       # Deep orange
    "secondary": "#FF6D00",     # Orange
    "accent": "#FFB300",        # Amber
    "success": "#00E676",       # Green
    "error": "#FF1744",         # Red
    "warning": "#FFD600",       # Yellow
    "info": "#40C4FF",          # Blue
    "dim": "#666666",           # Gray
    "user_prompt": "#FF9100",   # User input color
    "agent_response": "#E0E0E0", # Agent response color
}


# Global tracker for the active spinner so it can be paused from anywhere
ACTIVE_SPINNER = None

def pause_spinner():
    """Temporarily stop the active spinner (useful before taking input)."""
    global ACTIVE_SPINNER
    if ACTIVE_SPINNER:
        ACTIVE_SPINNER.stop()

def resume_spinner():
    """Resume the active spinner."""
    global ACTIVE_SPINNER
    if ACTIVE_SPINNER:
        ACTIVE_SPINNER.start()

class RageUI:
    """Manages all RAGE terminal output."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    # ── User / Agent Messages ─────────────────────────────────────────────

    def print_user_prompt(self):
        """Print the user input prompt indicator."""
        self.console.print(
            f"\n [bold {COLORS['user_prompt']}]❯[/bold {COLORS['user_prompt']}] ",
            end="",
        )

    def print_agent_thinking(self):
        """Show a thinking indicator."""
        class TrackedLive(Live):
            def __enter__(self):
                global ACTIVE_SPINNER
                ACTIVE_SPINNER = self
                return super().__enter__()
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                global ACTIVE_SPINNER
                ACTIVE_SPINNER = None
                return super().__exit__(exc_type, exc_val, exc_tb)

        return TrackedLive(
            Spinner("dots", text=Text(" Thinking...", style=f"dim {COLORS['accent']}")),
            console=self.console,
            transient=True,
        )

    def print_agent_response(self, text: str):
        """Print an agent response with markdown rendering."""
        self.console.print()
        md = Markdown(text)
        self.console.print(
            Panel(
                md,
                border_style=COLORS["primary"],
                padding=(1, 2),
                title="[bold]🔥 RAGE BORN[/bold]",
                title_align="left",
            )
        )

    def stream_agent_response(self, text_chunks, tool_name: str | None = None):
        """Stream agent response character by character for a live feel."""
        self.console.print()
        prefix = f"[bold {COLORS['primary']}]🔥 RAGE BORN[/bold {COLORS['primary']}]"
        if tool_name:
            prefix += f" [dim]» {tool_name}[/dim]"
        self.console.print(f"  {prefix}")
        self.console.print()

        full_text = ""
        for chunk in text_chunks:
            full_text += chunk
            sys.stdout.write(chunk)
            sys.stdout.flush()

        self.console.print()
        return full_text

    # ── Tool Execution ────────────────────────────────────────────────────

    def print_tool_call(self, tool_name: str, args: dict):
        """Show a tool being called."""
        self.console.print(
            f"  [bold {COLORS['accent']}]⚙ {tool_name}[/bold {COLORS['accent']}]"
            f"  [dim]{_summarize_args(args)}[/dim]"
        )

    def print_tool_result(self, tool_name: str, result: str, success: bool = True):
        """Show tool execution result."""
        color = COLORS["success"] if success else COLORS["error"]
        icon = "✓" if success else "✗"
        self.console.print(
            f"  [{color}]{icon}[/{color}] [dim]{tool_name}:[/dim] ",
            end="",
        )
        # Truncate long outputs
        if len(result) > 500:
            display = result[:500] + f"\n  [dim]... ({len(result)} chars total)[/dim]"
        else:
            display = result
        self.console.print(display)

    def print_command_output(self, output: str, title: str = "Output"):
        """Print command output in a styled panel."""
        if not output.strip():
            return
        self.console.print(
            Panel(
                output.strip(),
                border_style=COLORS["dim"],
                title=f"[dim]{title}[/dim]",
                title_align="left",
                padding=(0, 1),
            )
        )

    # ── Safety ────────────────────────────────────────────────────────────

    def print_safety_warning(self, command: str, explanation: str):
        """Show a safety warning for dangerous commands."""
        self.console.print()
        self.console.print(
            Panel(
                f"[bold {COLORS['warning']}]⚠ Dangerous Command Detected[/bold {COLORS['warning']}]\n\n"
                f"[bold]Command:[/bold] [red]{command}[/red]\n\n"
                f"[bold]Risk:[/bold] {explanation}\n\n"
                f"[dim]Type [bold]y[/bold] to approve, [bold]n[/bold] to cancel, "
                f"[bold]a[/bold] to always allow this pattern.[/dim]",
                border_style=COLORS["warning"],
                title="[bold]🛡 Safety Check[/bold]",
                title_align="left",
                padding=(1, 2),
            )
        )

    # ── Status / Info ─────────────────────────────────────────────────────

    def print_info(self, message: str):
        """Print an info message."""
        self.console.print(f"  [{COLORS['info']}]ℹ[/{COLORS['info']}] {message}")

    def print_success(self, message: str):
        """Print a success message."""
        self.console.print(
            f"  [{COLORS['success']}]✓[/{COLORS['success']}] {message}"
        )

    def print_error(self, message: str):
        """Print an error message."""
        self.console.print(
            f"  [{COLORS['error']}]✗[/{COLORS['error']}] [bold]{message}[/bold]"
        )

    def print_warning(self, message: str):
        """Print a warning message."""
        self.console.print(
            f"  [{COLORS['warning']}]⚠[/{COLORS['warning']}] {message}"
        )

    # ── Tables ────────────────────────────────────────────────────────────

    def print_task_table(self, tasks: list[dict]):
        """Print a table of background tasks."""
        table = Table(
            title="Background Tasks",
            border_style=COLORS["dim"],
            title_style=f"bold {COLORS['accent']}",
        )
        table.add_column("ID", style="bold", width=6)
        table.add_column("Command", style=COLORS["agent_response"])
        table.add_column("Status", width=12)
        table.add_column("Duration", style="dim", width=12)

        for task in tasks:
            status_color = {
                "running": COLORS["info"],
                "completed": COLORS["success"],
                "failed": COLORS["error"],
                "cancelled": COLORS["warning"],
            }.get(task.get("status", ""), COLORS["dim"])

            table.add_row(
                f"#{task.get('id', '?')}",
                task.get("command", "")[:50],
                f"[{status_color}]{task.get('status', 'unknown')}[/{status_color}]",
                task.get("duration", "—"),
            )

        self.console.print()
        self.console.print(table)
        self.console.print()

    def print_history_table(self, entries: list[dict]):
        """Print task history table."""
        table = Table(
            title="Task History",
            border_style=COLORS["dim"],
            title_style=f"bold {COLORS['accent']}",
        )
        table.add_column("#", style="bold", width=6)
        table.add_column("Command", style=COLORS["agent_response"])
        table.add_column("Status", width=12)
        table.add_column("Duration", style="dim", width=12)
        table.add_column("Time", style="dim", width=20)

        for entry in entries[-20:]:  # Show last 20
            status_color = COLORS["success"] if entry.get("success") else COLORS["error"]
            table.add_row(
                f"#{entry.get('id', '?')}",
                entry.get("command", "")[:40],
                f"[{status_color}]{'✓' if entry.get('success') else '✗'}[/{status_color}]",
                entry.get("duration", "—"),
                entry.get("timestamp", "—")[:19],
            )

        self.console.print()
        self.console.print(table)
        self.console.print()

    # ── Help ──────────────────────────────────────────────────────────────

    def print_help(self):
        """Print help menu."""
        self.console.print()
        self.console.print(
            Panel(
                "[bold]Available Commands[/bold]\n\n"
                f"  [bold {COLORS['accent']}]/help[/bold {COLORS['accent']}]        Show this help menu\n"
                f"  [bold {COLORS['accent']}]/tasks[/bold {COLORS['accent']}]       Show background tasks\n"
                f"  [bold {COLORS['accent']}]/history[/bold {COLORS['accent']}]     Show task history\n"
                f"  [bold {COLORS['accent']}]/memory[/bold {COLORS['accent']}]      Show remembered context\n"
                f"  [bold {COLORS['accent']}]/terminals[/bold {COLORS['accent']}]   Show active terminal sessions\n"
                f"  [bold {COLORS['accent']}]/browser[/bold {COLORS['accent']}]     Show browser tabs & status\n"
                f"  [bold {COLORS['accent']}]/browseurl[/bold {COLORS['accent']}]    Open a URL in the browser\n"
                f"  [bold {COLORS['accent']}]/searchq[/bold {COLORS['accent']}]      Google search from terminal\n"
                f"  [bold {COLORS['accent']}]/glogin[/bold {COLORS['accent']}]      Log in to Google Workspace\n"
                f"  [bold {COLORS['accent']}]/model[/bold {COLORS['accent']}]       Select AI model (LLM)\n"
                f"  [bold {COLORS['accent']}]/plan[/bold {COLORS['accent']}]        Autonomous planning mode (e.g. /plan build a todo app)\n"
                f"  [bold {COLORS['accent']}]/clear[/bold {COLORS['accent']}]       Clear the screen\n"
                f"  [bold {COLORS['accent']}]/config[/bold {COLORS['accent']}]      Show current configuration\n"
                f"  [bold {COLORS['accent']}]/exit[/bold {COLORS['accent']}]        Exit RAGE BORN\n\n"
                "[dim]Or just type naturally — RAGE BORN will figure out what to do.[/dim]",
                border_style=COLORS["primary"],
                title="[bold]📖 Help[/bold]",
                title_align="left",
                padding=(1, 2),
            )
        )
        self.console.print()


def _summarize_args(args: dict) -> str:
    """Create a short summary of tool arguments."""
    parts = []
    for key, val in args.items():
        val_str = str(val)
        if len(val_str) > 60:
            val_str = val_str[:57] + "..."
        parts.append(f"{key}={val_str}")
    return ", ".join(parts)
