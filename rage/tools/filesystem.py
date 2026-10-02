"""
RAGE File System Tool — Read, write, list, and search files.
"""

import os
import glob
from pathlib import Path
from rage.tools.base import BaseTool, ToolResult


class ReadFileTool(BaseTool):
    """Read file contents."""

    name = "read_file"
    description = (
        "Read the contents of a file. Returns the full file text. "
        "Use this to inspect code, configs, logs, or any text file."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute or relative path to the file",
            },
            "start_line": {
                "type": "integer",
                "description": "Start line (1-indexed, optional)",
            },
            "end_line": {
                "type": "integer",
                "description": "End line (1-indexed, optional)",
            },
        },
        "required": ["path"],
    }

    def execute(self, path: str, start_line: int = 0, end_line: int = 0) -> ToolResult:
        path = os.path.expanduser(path)
        try:
            if not os.path.exists(path):
                return ToolResult(success=False, output="", error=f"File not found: {path}")

            if not os.path.isfile(path):
                return ToolResult(success=False, output="", error=f"Not a file: {path}")

            # Check file size (skip huge files)
            size = os.path.getsize(path)
            if size > 1_000_000:  # 1MB
                return ToolResult(
                    success=False,
                    output="",
                    error=f"File too large ({size:,} bytes). Use search_files or read specific line ranges.",
                )

            with open(path, "r", errors="replace") as f:
                lines = f.readlines()

            if start_line > 0 and end_line > 0:
                selected = lines[start_line - 1 : end_line]
                content = "".join(selected)
                header = f"[Lines {start_line}-{end_line} of {len(lines)}]\n"
            else:
                content = "".join(lines)
                header = f"[{len(lines)} lines, {size:,} bytes]\n"

            return ToolResult(success=True, output=header + content)

        except PermissionError:
            return ToolResult(success=False, output="", error=f"Permission denied: {path}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class WriteFileTool(BaseTool):
    """Write content to a file."""

    name = "write_file"
    description = (
        "Write content to a file. Creates the file and parent directories if needed. "
        "Use this to create new files or overwrite existing ones."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to write",
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file",
            },
            "append": {
                "type": "boolean",
                "description": "If true, append to file instead of overwriting (default: false)",
            },
        },
        "required": ["path", "content"],
    }

    def execute(self, path: str, content: str, append: bool = False) -> ToolResult:
        path = os.path.expanduser(path)
        try:
            # Create parent dirs
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

            mode = "a" if append else "w"
            with open(path, mode) as f:
                f.write(content)

            action = "Appended to" if append else "Written to"
            size = os.path.getsize(path)
            return ToolResult(
                success=True,
                output=f"{action} {path} ({size:,} bytes)",
            )

        except PermissionError:
            return ToolResult(success=False, output="", error=f"Permission denied: {path}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class ListDirectoryTool(BaseTool):
    """List directory contents."""

    name = "list_directory"
    description = (
        "List files and directories at a given path. "
        "Shows file sizes and types. Use to explore project structure."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path to list (default: current directory)",
            },
            "show_hidden": {
                "type": "boolean",
                "description": "Show hidden files (default: false)",
            },
        },
        "required": [],
    }

    def execute(self, path: str = ".", show_hidden: bool = False) -> ToolResult:
        path = os.path.expanduser(path)
        try:
            if not os.path.isdir(path):
                return ToolResult(success=False, output="", error=f"Not a directory: {path}")

            entries = sorted(os.listdir(path))
            if not show_hidden:
                entries = [e for e in entries if not e.startswith(".")]

            lines = [f"📁 {os.path.abspath(path)}/", ""]
            for entry in entries:
                full = os.path.join(path, entry)
                if os.path.isdir(full):
                    count = len(os.listdir(full))
                    lines.append(f"  📂 {entry}/  ({count} items)")
                else:
                    size = os.path.getsize(full)
                    if size < 1024:
                        sz = f"{size}B"
                    elif size < 1_048_576:
                        sz = f"{size / 1024:.1f}KB"
                    else:
                        sz = f"{size / 1_048_576:.1f}MB"
                    lines.append(f"  📄 {entry}  ({sz})")

            if not entries:
                lines.append("  (empty directory)")

            return ToolResult(success=True, output="\n".join(lines))

        except PermissionError:
            return ToolResult(success=False, output="", error=f"Permission denied: {path}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class SearchFilesTool(BaseTool):
    """Search for text patterns in files."""

    name = "search_files"
    description = (
        "Search for a text pattern across files in a directory. "
        "Similar to grep. Returns matching lines with file paths and line numbers."
    )
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Text pattern to search for",
            },
            "path": {
                "type": "string",
                "description": "Directory to search in (default: current directory)",
            },
            "file_pattern": {
                "type": "string",
                "description": "File glob pattern, e.g. '*.py' (default: all files)",
            },
        },
        "required": ["pattern"],
    }

    def execute(self, pattern: str, path: str = ".",
                file_pattern: str = "**/*") -> ToolResult:
        path = os.path.expanduser(path)
        try:
            if not os.path.isdir(path):
                return ToolResult(success=False, output="", error=f"Not a directory: {path}")

            matches = []
            search_glob = os.path.join(path, file_pattern)

            for filepath in glob.glob(search_glob, recursive=True):
                if not os.path.isfile(filepath):
                    continue
                # Skip binary files
                try:
                    with open(filepath, "r", errors="strict") as f:
                        for lineno, line in enumerate(f, 1):
                            if pattern.lower() in line.lower():
                                matches.append(
                                    f"  {filepath}:{lineno}: {line.rstrip()}"
                                )
                                if len(matches) >= 50:
                                    break
                except (UnicodeDecodeError, PermissionError):
                    continue

                if len(matches) >= 50:
                    break

            if not matches:
                return ToolResult(
                    success=True,
                    output=f"No matches found for '{pattern}' in {path}",
                )

            header = f"Found {len(matches)} matches for '{pattern}':\n"
            result = header + "\n".join(matches)
            if len(matches) >= 50:
                result += "\n  ... (results truncated at 50)"

            return ToolResult(success=True, output=result)

        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
