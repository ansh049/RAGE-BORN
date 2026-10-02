"""
RAGE Configuration Management.

Manages ~/.rage/ directory, config.json, and first-run setup.
"""

import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass


RAGE_DIR = Path.home() / ".rage"
CONFIG_FILE = RAGE_DIR / "config.json"
HISTORY_FILE = RAGE_DIR / "history.json"
MEMORY_FILE = RAGE_DIR / "memory.json"
LOGS_DIR = RAGE_DIR / "logs"
BROWSER_PROFILE_DIR = RAGE_DIR / "browser_profile"

DOWNLOADS_DIR = RAGE_DIR / "downloads"
SCREENSHOTS_DIR = RAGE_DIR / "screenshots"

DEFAULT_CONFIG = {
    "api_key": "",
    "github_token": "",
    "groq_api_key": "",
    "nvidia_api_key": "",
    "api_url": "https://lightning.ai/api/v1/chat/completions",
    "github_api_url": "https://models.github.ai/inference/chat/completions",
    "groq_api_url": "https://api.groq.com/openai/v1/chat/completions",
    "nvidia_api_url": "https://integrate.api.nvidia.com/v1/chat/completions",
    "model": "lightning-ai/gemma-4-31B-it",
    "max_tokens": 32768,
    "temperature": 0.7,
    "safety_confirm_destructive": True,
    "auto_approve_patterns": [],
    "theme": "dark",
    "browser_headless": True,
    "browser_viewport_width": 1920,
    "browser_viewport_height": 1080,
}

AVAILABLE_MODELS = [
    "lightning-ai/gemma-4-31B-it",
    "lightning-ai/minimax-m2.5",
    "google/gemini-3.1-flash-lite-preview",
    "openai/gpt-4o",
    "openai/gpt-4.1",
    "meta/Meta-Llama-3.1-405B-Instruct",
    "meta/Llama-3.3-70B-Instruct",
    "meta/Llama-4-Maverick-17B-128E-Instruct-FP8",
    "meta/Llama-3.2-90B-Vision-Instruct",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "z-ai/glm-5.2",
    "minimaxai/minimax-m3",
    "minimaxai/minimax-m2.7",
    "moonshotai/kimi-k2.6",
    "google/gemma-4-31b-it",
    "anthropic/claude-haiku-4-5-20251001",
    "google/gemini-3.5-flash",
]


def ensure_rage_dirs():
    """Create all required RAGE directories."""
    RAGE_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load configuration from ~/.rage/config.json."""
    ensure_rage_dirs()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
            # Merge with defaults to pick up new keys
            config = {**DEFAULT_CONFIG, **saved}
            return config
        except (json.JSONDecodeError, IOError):
            return dict(DEFAULT_CONFIG)
    return dict(DEFAULT_CONFIG)


def save_config(config: dict):
    """Save configuration to ~/.rage/config.json."""
    ensure_rage_dirs()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_api_key(config: dict) -> str:
    """Get API key from config or environment."""
    # Environment variable takes priority
    env_key = os.environ.get("RAGE_API_KEY", "")
    if env_key:
        return env_key
    return config.get("api_key", "")

def get_github_token(config: dict) -> str:
    """Get GitHub token from config or environment."""
    env_key = os.environ.get("GITHUB_TOKEN", "")
    if env_key:
        return env_key
    return config.get("github_token", "")


def get_groq_api_key(config: dict) -> str:
    """Get Groq API key from config or environment."""
    env_key = os.environ.get("GROQ_API_KEY", "")
    if env_key:
        return env_key
    return config.get("groq_api_key", "")

def get_nvidia_api_key(config: dict) -> str:
    """Get NVIDIA API key from config or environment."""
    env_key = os.environ.get("NVIDIA_API_KEY", "")
    if env_key:
        return env_key
    return config.get("nvidia_api_key", "")


def first_run_setup() -> dict:
    """Interactive first-run setup. Returns config."""
    from rich.console import Console
    from rich.prompt import Prompt

    console = Console()

    console.print("\n[bold cyan]⚡ Welcome to RAGE BORN — First-Time Setup[/bold cyan]\n")
    console.print("[dim]Let's configure your AI agent.[/dim]\n")

    config = dict(DEFAULT_CONFIG)

    # API Key
    api_key = Prompt.ask(
        "[bold yellow]🔑 Enter your Lightning AI API key[/bold yellow]",
        default="",
        console=console,
    )
    if api_key:
        config["api_key"] = api_key
    else:
        console.print(
            "[dim]You can also set RAGE_API_KEY environment variable later.[/dim]"
        )

    # Model Selection
    console.print("\n[bold yellow]🤖 Select a Model:[/bold yellow]")
    for i, m in enumerate(AVAILABLE_MODELS, 1):
        console.print(f"  {i}. {m}")
    
    choices = [str(i) for i in range(1, len(AVAILABLE_MODELS) + 1)]
    model_choice = Prompt.ask(
        f"Enter choice (1-{len(AVAILABLE_MODELS)})",
        choices=choices,
        default="1",
        console=console,
    )
    
    config["model"] = AVAILABLE_MODELS[int(model_choice) - 1]

    save_config(config)
    console.print("\n[bold green]✅ Configuration saved to ~/.rage/config.json[/bold green]\n")
    return config
