"""
RAGE BORN Safety System — Dangerous Command Detection.

Detects potentially destructive shell commands and requires user confirmation
before execution. Supports "always allow" patterns for trusted users.
"""

import re
from rage.config import load_config, save_config


# ── Dangerous Patterns ────────────────────────────────────────────────────────
# Each pattern has a regex, a human-readable risk explanation, and a severity.

DANGEROUS_PATTERNS = [
    {
        "pattern": r"\brm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+|.*-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+)(/|~|\$HOME|\.\.|\.)",
        "risk": "Recursive forced deletion of important directories. This can permanently destroy files.",
        "severity": "critical",
    },
    {
        "pattern": r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*\s+",
        "risk": "Recursive file deletion. Files will be permanently removed.",
        "severity": "high",
    },
    {
        "pattern": r"\brm\s+-[a-zA-Z]*f[a-zA-Z]*\s+",
        "risk": "Forced file deletion without confirmation prompts.",
        "severity": "medium",
    },
    {
        "pattern": r"\brm\s+",
        "risk": "File deletion. The file will be permanently removed.",
        "severity": "low",
    },
    {
        "pattern": r"\bmv\s+",
        "risk": "Moving or renaming files. Could overwrite existing files if not careful.",
        "severity": "low",
    },
    {
        "pattern": r"\bcp\s+",
        "risk": "Copying files. Could overwrite existing files at the destination.",
        "severity": "low",
    },
    {
        "pattern": r"\bmkdir\s+",
        "risk": "Creating new directories on the filesystem.",
        "severity": "low",
    },
    {
        "pattern": r"\brmdir\s+",
        "risk": "Removing directories from the filesystem.",
        "severity": "low",
    },
    {
        "pattern": r"\bdd\s+",
        "risk": "Low-level disk copy. Can overwrite entire disks and cause data loss.",
        "severity": "critical",
    },
    {
        "pattern": r"\bmkfs\b",
        "risk": "Filesystem formatting. This will erase all data on the target device.",
        "severity": "critical",
    },
    {
        "pattern": r"\bfdisk\b|\bparted\b|\bgdisk\b",
        "risk": "Disk partitioning tool. Can modify or destroy partition tables.",
        "severity": "critical",
    },
    {
        "pattern": r"\bshutdown\b|\breboot\b|\bpoweroff\b|\binit\s+[06]\b",
        "risk": "System shutdown/reboot. This will terminate all running processes.",
        "severity": "high",
    },
    {
        "pattern": r"\bsystemctl\s+(disable|stop|mask)\s+",
        "risk": "Disabling/stopping system services. May affect system stability.",
        "severity": "high",
    },
    {
        "pattern": r"\biptables\b|\bnftables\b|\bufw\s+(disable|reset)\b",
        "risk": "Firewall modification. May expose the system to network threats.",
        "severity": "high",
    },
    {
        "pattern": r"\bchmod\s+[0-7]*777\b|\bchmod\s+-R\s+",
        "risk": "Changing file permissions broadly. May create security vulnerabilities.",
        "severity": "medium",
    },
    {
        "pattern": r"\bchown\s+-R\s+",
        "risk": "Recursively changing file ownership.",
        "severity": "medium",
    },
    {
        "pattern": r">\s*/dev/sd[a-z]|>\s*/dev/nvme|>\s*/dev/vd[a-z]",
        "risk": "Writing directly to a block device. Can destroy all data on the disk.",
        "severity": "critical",
    },
    {
        "pattern": r"\bcurl\b.*\|\s*(sudo\s+)?(ba)?sh",
        "risk": "Piping remote script to shell. The script contents are unverified.",
        "severity": "high",
    },
    {
        "pattern": r"\bwget\b.*\|\s*(sudo\s+)?(ba)?sh",
        "risk": "Piping remote script to shell. The script contents are unverified.",
        "severity": "high",
    },
    {
        "pattern": r"\bsudo\s+rm\b",
        "risk": "Deleting files with root privileges.",
        "severity": "high",
    },
    {
        "pattern": r":(){ :\|:& };:",
        "risk": "Fork bomb. This will crash the system by exhausting resources.",
        "severity": "critical",
    },
    {
        "pattern": r"\bkill\s+-9\s+(-1|1)\b|\bkillall\b",
        "risk": "Killing processes aggressively. May terminate important system processes.",
        "severity": "high",
    },
]


class SafetyChecker:
    """Check commands for dangerous patterns and manage user approvals."""

    def __init__(self):
        config = load_config()
        self.auto_approve_patterns: list[str] = config.get("auto_approve_patterns", [])

    def check_command(self, command: str) -> dict | None:
        """
        Check if a command matches any dangerous pattern.

        Returns None if safe, or a dict with {pattern, risk, severity} if dangerous.
        """
        # Check auto-approve list first
        for approved in self.auto_approve_patterns:
            if re.search(approved, command, re.IGNORECASE):
                return None

        # Check all dangerous patterns
        for entry in DANGEROUS_PATTERNS:
            if re.search(entry["pattern"], command, re.IGNORECASE):
                return {
                    "pattern": entry["pattern"],
                    "risk": entry["risk"],
                    "severity": entry["severity"],
                    "command": command,
                }

        return None

    def add_auto_approve(self, pattern: str):
        """Add a pattern to the auto-approve list and persist it."""
        if pattern not in self.auto_approve_patterns:
            self.auto_approve_patterns.append(pattern)
            config = load_config()
            config["auto_approve_patterns"] = self.auto_approve_patterns
            save_config(config)

    def request_approval(self, danger_info: dict) -> str:
        """
        Ask the user for approval of a dangerous command.

        Returns: 'y' (approve once), 'a' (always approve), 'n' (deny)
        """
        from rich.console import Console
        from rage.ui import RageUI, pause_spinner, resume_spinner

        console = Console()
        ui = RageUI(console)
        
        pause_spinner()
        try:
            ui.print_safety_warning(danger_info["command"], danger_info["risk"])

            while True:
                choice = input("  [y/n/a] > ").strip().lower()
                if choice in ("y", "yes"):
                    return "y"
                elif choice in ("a", "always"):
                    # Escape the command for use as a regex pattern
                    escaped = re.escape(danger_info["command"])
                    self.add_auto_approve(escaped)
                    ui.print_success("Pattern added to auto-approve list.")
                    return "a"
                elif choice in ("n", "no", ""):
                    return "n"
                else:
                    console.print("  [dim]Please enter y, n, or a.[/dim]")
        finally:
            resume_spinner()
