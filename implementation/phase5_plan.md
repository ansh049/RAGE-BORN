# Phase 5 Implementation Plan: Autonomous Mode & Advanced Workflows

## Goal Description
Transform RAGE from an interactive-only assistant into a fully autonomous, long-running agent capable of syncing state across devices and performing self-maintenance.

## Proposed Changes

### 1. Autonomous Loop Mode (`/auto`)
- **Mechanism**: Introduce a new CLI command `/auto <goal>`.
- **Behavior**: RAGE will enter a background loop, executing tool after tool without pausing for user input, until the `goal` is met. 
- **Safety Overrides**: If it hits a dangerous command (from `safety.py`), it will pause the autonomous loop and wait for user confirmation.

### 2. Cross-Device Memory Sync
- **Mechanism**: Add a `sync` method to `rage/memory.py`.
- **Providers**: Support AWS S3 or Google Drive.
- **Behavior**: Pushes `~/.rage/memory.json` to the cloud and pulls the latest version on startup, allowing memory to follow the user across machines.

### 3. Self-Updating RAGE
- Add a tool `self_update` which allows RAGE to `git pull` from its own repository and run `pip install -e .` on itself.
- Requires gracefully restarting the process state in `cli.py`.

### 4. Advanced Desktop Vision (Optional)
- Move beyond Playwright by integrating OS-level screenshot tools (e.g., `scrot` or `grim` on Linux) so RAGE can see the entire desktop environment, not just the browser.

## Verification Plan
### Automated Tests
- Test the `/auto` loop against a deterministic mock tool to ensure it terminates when the goal is achieved.
- Verify `memory.json` resolves conflicts safely during sync.

### Manual Verification
- Run `/auto create a tic tac toe game in python, test it, and save it`. RAGE should accomplish the entire sequence without user intervention.
