# RAGE — AI Terminal Agent

Build a premium, open-source AI terminal agent (like Claude Code / Gemini CLI) that can execute commands, automate browsers, manage background tasks, and act as a complete AI operating companion for Linux.

**LLM Backend:** Lightning AI API (`lightning-ai/gemma-4-31B-it`) via OpenAI-compatible chat completions endpoint.

## User Review Required

> [!IMPORTANT]
> **API Key Exposure** — Your API key `sk-lit-5f7ee0b1-...` is in the project files. The plan stores it in a local config file (`~/.rage/config.json`). Confirm this is acceptable, or should we use an environment variable only?

> [!IMPORTANT]
> **Scope of Phase 1** — This is a very large project. I propose building it in **phases**, shipping a working MVP first and layering features on top. See the phased breakdown below.

> [!WARNING]
> **Playwright dependency** — Playwright requires `playwright install` to download browser binaries (~200MB). This will be part of the install script.

## Open Questions

1. **Python version** — Should we target Python 3.10+ or 3.12+?
2. **Package name on PyPI** — `rage-cli` as mentioned in your spec? (We'll check availability later.)
3. **Google Workspace** — These features require OAuth2 credentials. Do you have a Google Cloud project set up, or should we defer Google Workspace/Meet to a later phase?
4. **Priority** — Which features do you want working FIRST? My recommendation is the phased approach below.

---

## Phased Delivery

### Phase 1 — Core Agent (THIS SESSION) ✅
Everything needed for a working, impressive terminal AI agent:

| Feature | Description |
|---|---|
| **Branded CLI** | Premium ASCII banner, colored output, status bar |
| **Chat Loop** | Interactive REPL with streaming responses |
| **Tool System** | Modular tool/plugin architecture |
| **Terminal Tool** | Execute shell commands, multi-tab terminal sessions |
| **File System Tool** | Read/write/search files |
| **Safety System** | Dangerous command detection + user confirmation |
| **Background Tasks** | Run long tasks in background, track progress, logs |
| **Task History** | Persistent log of all executed tasks |
| **Memory** | Persistent user preferences & context |
| **Installer** | `pip install` + `curl` one-liner install script |

### Phase 2 — Browser & Web (Future)
| Feature | Description |
|---|---|
| **Playwright Browser** | Persistent profile, browsing, form filling |
| **Web Search** | Google search integration |
| **Page Interaction** | Read, summarize, interact with web pages |

### Phase 3 — Google Workspace & Advanced (Future)
| Feature | Description |
|---|---|
| **Google Docs/Sheets/Slides** | Create, read, edit documents |
| **Gmail** | Send, read, search emails |
| **Google Meet** | Create/join meetings |
| **Google Calendar** | Schedule events |

### Phase 4 — Ecosystem (Future)
| Feature | Description |
|---|---|
| **Plugin marketplace** | Community plugins |
| **Git/GitHub deep integration** | PR reviews, issue management |
| **Docker/K8s tools** | Container management |
| **VS Code integration** | Editor bridge |

---

## Proposed Changes — Phase 1

### Project Structure

```
/home/rohit/Coding/AI IDE/
├── rage/
│   ├── __init__.py
│   ├── __main__.py          # Entry point: `python -m rage`
│   ├── cli.py               # Main CLI REPL, banner, input loop
│   ├── agent.py             # Core agent: LLM interaction, tool orchestration
│   ├── llm.py               # Lightning AI API client (streaming)
│   ├── config.py            # Configuration management (~/.rage/)
│   ├── memory.py            # Persistent memory system
│   ├── safety.py            # Dangerous command detection
│   ├── history.py           # Task history persistence
│   ├── banner.py            # ASCII art banner + branding
│   ├── ui.py                # Rich terminal UI (colors, panels, markdown)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py          # Base tool class (plugin interface)
│   │   ├── registry.py      # Tool registry & discovery
│   │   ├── terminal.py      # Shell command execution + multi-tab
│   │   ├── filesystem.py    # File read/write/search
│   │   ├── git_tool.py      # Git operations
│   │   └── browser.py       # Placeholder for Phase 2
│   └── tasks/
│       ├── __init__.py
│       ├── manager.py       # Background task manager
│       └── models.py        # Task data models
├── setup.py                 # Package setup
├── pyproject.toml           # Modern Python packaging
├── requirements.txt         # Dependencies
├── install.sh               # curl-based installer
├── README.md                # Documentation
└── .gitignore
```

---

### Core Components

#### [NEW] [pyproject.toml](file:///home/rohit/Coding/AI%20IDE/pyproject.toml)
Modern Python package config. Defines `rage` as the CLI entry point, dependencies (`requests`, `rich`, `prompt_toolkit`, `pyfiglet`).

#### [NEW] [requirements.txt](file:///home/rohit/Coding/AI%20IDE/requirements.txt)
```
requests>=2.31.0
rich>=13.0.0
prompt_toolkit>=3.0.0
pyfiglet>=1.0.0
```

---

### Branding & UI

#### [NEW] [rage/banner.py](file:///home/rohit/Coding/AI%20IDE/rage/banner.py)
- Custom ASCII art "RAGE" logo with gradient colors (red → orange → yellow, inspired by the name)
- Version display, model info, status indicators
- Uses `rich` library for premium terminal rendering

#### [NEW] [rage/ui.py](file:///home/rohit/Coding/AI%20IDE/rage/ui.py)
- Rich-powered output: markdown rendering, syntax highlighting, panels, progress bars
- Streaming response display (character-by-character like Claude/Gemini)
- Status bar showing model, context, active tasks

---

### Agent Core

#### [NEW] [rage/llm.py](file:///home/rohit/Coding/AI%20IDE/rage/llm.py)
- Lightning AI API client
- Streaming chat completions
- System prompt with tool definitions (function calling via structured output)
- Conversation history management

#### [NEW] [rage/agent.py](file:///home/rohit/Coding/AI%20IDE/rage/agent.py)
- Core agent loop: receive user input → plan → call tools → return result
- Tool call parsing from LLM responses (JSON-based function calling)
- Multi-step reasoning (agent can chain multiple tool calls)
- Error recovery and retry logic

#### [NEW] [rage/safety.py](file:///home/rohit/Coding/AI%20IDE/rage/safety.py)
- Pattern-based dangerous command detection (`rm -rf`, `dd`, `mkfs`, `shutdown`, etc.)
- User confirmation prompts with explanation of risk
- "Always allow" trust system per command pattern

---

### Tool System

#### [NEW] [rage/tools/base.py](file:///home/rohit/Coding/AI%20IDE/rage/tools/base.py)
```python
class BaseTool:
    name: str
    description: str
    parameters: dict  # JSON Schema
    
    def execute(self, **kwargs) -> ToolResult
    def get_schema(self) -> dict  # For LLM function calling
```

#### [NEW] [rage/tools/registry.py](file:///home/rohit/Coding/AI%20IDE/rage/tools/registry.py)
- Auto-discovery of tool classes
- Register/unregister tools dynamically
- Generate combined tool schema for LLM system prompt

#### [NEW] [rage/tools/terminal.py](file:///home/rohit/Coding/AI%20IDE/rage/tools/terminal.py)
- `run_command` — Execute a shell command and return output
- `create_terminal` — Create a named terminal session (tab)
- `list_terminals` — Show active terminal sessions
- `switch_terminal` — Switch active terminal
- Uses `subprocess` with `asyncio` for non-blocking execution
- Safety check integration before execution

#### [NEW] [rage/tools/filesystem.py](file:///home/rohit/Coding/AI%20IDE/rage/tools/filesystem.py)
- `read_file` — Read file contents
- `write_file` — Write/create files
- `list_directory` — List directory contents
- `search_files` — Grep/find across files

#### [NEW] [rage/tools/git_tool.py](file:///home/rohit/Coding/AI%20IDE/rage/tools/git_tool.py)
- `git_status`, `git_commit`, `git_push`, `git_log`, `git_diff`
- Wraps git CLI commands through the terminal tool

---

### Background Tasks

#### [NEW] [rage/tasks/manager.py](file:///home/rohit/Coding/AI%20IDE/rage/tasks/manager.py)
- Run commands in background threads
- Task ID assignment, progress tracking
- Live log capture (stdout/stderr)
- Completion notifications
- Cancel/restart support

#### [NEW] [rage/tasks/models.py](file:///home/rohit/Coding/AI%20IDE/rage/tasks/models.py)
- `Task` dataclass: id, command, status, start_time, end_time, output, error, logs

---

### Persistence

#### [NEW] [rage/config.py](file:///home/rohit/Coding/AI%20IDE/rage/config.py)
- Manages `~/.rage/config.json` — API key, model selection, preferences
- First-run setup wizard

#### [NEW] [rage/memory.py](file:///home/rohit/Coding/AI%20IDE/rage/memory.py)
- Stores user preferences, project context, learned facts in `~/.rage/memory.json`
- Injected into LLM system prompt

#### [NEW] [rage/history.py](file:///home/rohit/Coding/AI%20IDE/rage/history.py)
- Persistent task history in `~/.rage/history.json`
- Stores: command, timestamp, duration, status, output, errors

---

### Entry Points

#### [NEW] [rage/__main__.py](file:///home/rohit/Coding/AI%20IDE/rage/__main__.py)
- `python -m rage` entry point
- Argument parsing (direct command vs interactive mode)

#### [NEW] [rage/cli.py](file:///home/rohit/Coding/AI%20IDE/rage/cli.py)
- Main REPL loop with `prompt_toolkit`
- Banner display on startup
- Command history, auto-completion
- Special commands: `/help`, `/tasks`, `/history`, `/memory`, `/clear`, `/exit`

---

### Installation

#### [NEW] [install.sh](file:///home/rohit/Coding/AI%20IDE/install.sh)
```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USER/rage/main/install.sh | bash
```
- Checks Python version
- Creates virtualenv or installs globally
- Installs dependencies
- Creates `~/.rage/` config directory
- Adds `rage` to PATH

#### [NEW] [setup.py](file:///home/rohit/Coding/AI%20IDE/setup.py) + [pyproject.toml](file:///home/rohit/Coding/AI%20IDE/pyproject.toml)
- `pip install rage-cli` support
- Console script entry point: `rage` → `rage.cli:main`

---

## Verification Plan

### Automated Tests
```bash
# Install in development mode
pip install -e .

# Run RAGE
rage

# Test direct command mode
rage "What is my current directory?"

# Test tool execution
# (Inside RAGE) "List the files in this directory"
# (Inside RAGE) "Create a file called hello.txt with 'Hello World'"
# (Inside RAGE) "Run background task: sleep 5 && echo done"
# (Inside RAGE) "Show task history"
```

### Manual Verification
- Verify the ASCII banner renders correctly with colors
- Verify streaming responses work
- Verify dangerous command detection triggers for `rm -rf /`
- Verify background tasks run and report completion
- Verify memory persists between sessions
- Verify multi-terminal tab management works
