# RAGE — Phase 1 Build Walkthrough

## What Was Built

A fully working AI-powered terminal agent called **RAGE**, inspired by Claude Code and Gemini CLI. Built in Python with a modular plugin architecture.

### 20 Source Files Created

| File | Purpose |
|---|---|
| [pyproject.toml](file:///home/rohit/Coding/AI%20IDE/pyproject.toml) | Package config, `rage` CLI entry point |
| [requirements.txt](file:///home/rohit/Coding/AI%20IDE/requirements.txt) | Dependencies |
| [setup.py](file:///home/rohit/Coding/AI%20IDE/setup.py) | Legacy packaging |
| [.gitignore](file:///home/rohit/Coding/AI%20IDE/.gitignore) | Git ignore rules |
| [install.sh](file:///home/rohit/Coding/AI%20IDE/install.sh) | Curl one-liner installer |
| [README.md](file:///home/rohit/Coding/AI%20IDE/README.md) | Full documentation |
| [rage/__init__.py](file:///home/rohit/Coding/AI%20IDE/rage/__init__.py) | Package version |
| [rage/__main__.py](file:///home/rohit/Coding/AI%20IDE/rage/__main__.py) | `python -m rage` entry |
| [rage/cli.py](file:///home/rohit/Coding/AI%20IDE/rage/cli.py) | Interactive REPL with slash commands |
| [rage/agent.py](file:///home/rohit/Coding/AI%20IDE/rage/agent.py) | Core agent loop — LLM ↔ tools orchestration |
| [rage/llm.py](file:///home/rohit/Coding/AI%20IDE/rage/llm.py) | Lightning AI API client with streaming |
| [rage/config.py](file:///home/rohit/Coding/AI%20IDE/rage/config.py) | `~/.rage/` config management |
| [rage/banner.py](file:///home/rohit/Coding/AI%20IDE/rage/banner.py) | Premium ASCII banner with gradient |
| [rage/ui.py](file:///home/rohit/Coding/AI%20IDE/rage/ui.py) | Rich terminal UI components |
| [rage/safety.py](file:///home/rohit/Coding/AI%20IDE/rage/safety.py) | Dangerous command detection |
| [rage/memory.py](file:///home/rohit/Coding/AI%20IDE/rage/memory.py) | Persistent memory across sessions |
| [rage/history.py](file:///home/rohit/Coding/AI%20IDE/rage/history.py) | Command history log |
| [rage/tools/base.py](file:///home/rohit/Coding/AI%20IDE/rage/tools/base.py) | Base tool/plugin class |
| [rage/tools/registry.py](file:///home/rohit/Coding/AI%20IDE/rage/tools/registry.py) | Tool registry & factory |
| [rage/tools/terminal.py](file:///home/rohit/Coding/AI%20IDE/rage/tools/terminal.py) | Shell execution + multi-tab sessions |
| [rage/tools/filesystem.py](file:///home/rohit/Coding/AI%20IDE/rage/tools/filesystem.py) | File read/write/list/search |
| [rage/tools/git_tool.py](file:///home/rohit/Coding/AI%20IDE/rage/tools/git_tool.py) | Git operations |
| [rage/tools/browser.py](file:///home/rohit/Coding/AI%20IDE/rage/tools/browser.py) | Browser placeholder (Phase 2) |
| [rage/tasks/manager.py](file:///home/rohit/Coding/AI%20IDE/rage/tasks/manager.py) | Background task manager |
| [rage/tasks/models.py](file:///home/rohit/Coding/AI%20IDE/rage/tasks/models.py) | Task data models |

---

## Architecture

```
User Input → CLI (prompt_toolkit) → Agent → LLM (Lightning AI / Gemma)
                                      ↕
                              Tool Registry
                         ┌──────┼──────┐
                    Terminal  Files   Git
                         │
                    Safety Check → User Approval
                         │
                    Background Task Manager
                         │
                    History + Memory (persistent)
```

---

## Verification Results

All tests passed:

- ✅ **Package install** — `pip install -e .` succeeds, `rage` command available
- ✅ **Banner rendering** — Gradient ASCII art renders in terminal
- ✅ **LLM API** — Lightning AI API responds correctly
- ✅ **Tools** — Terminal, filesystem, git tools all execute correctly
- ✅ **Safety** — Detects `rm -rf`, `dd`, `mkfs`, `shutdown`, `curl|bash` as dangerous; allows `echo`, `ls`
- ✅ **Full agent loop** — User → LLM → tool execution → response works end-to-end
- ✅ **`rage` CLI** — Both interactive and direct command mode work

---

## How to Use

```bash
# Interactive mode
rage

# Direct command
rage "List files in the current directory"
rage "Install Node.js"

# Inside RAGE
/help       — show commands
/tasks      — show background tasks
/history    — show command history
/memory     — show what RAGE remembers
/terminals  — show terminal sessions
/exit       — quit
```
