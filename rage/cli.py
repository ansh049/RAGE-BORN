"""
RAGE BORN CLI — Main Interactive REPL.

The primary user interface for RAGE. Handles:
- Startup (banner, config check)
- Interactive chat loop with prompt_toolkit
- Slash commands (/help, /tasks, /history, etc.)
- Direct command mode (rage "do something")
- Graceful shutdown
"""

import sys
import os
import signal
from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style as PTStyle

from rage import __version__
from rage.banner import print_banner
from rage.config import (
    load_config,
    save_config,
    get_api_key,
    get_github_token,
    get_groq_api_key,
    get_nvidia_api_key,
    first_run_setup,
    ensure_rage_dirs,
    RAGE_DIR,
)
from rage.llm import LLMClient
from rage.agent import Agent
from rage.tools.registry import create_default_registry
from rage.memory import Memory
from rage.history import History
from rage.tasks.manager import TaskManager
from rage.ui import RageUI


# ── Prompt Toolkit Style ─────────────────────────────────────────────────────
PT_STYLE = PTStyle.from_dict({
    "prompt": "#FF6D00 bold",
    "": "#E0E0E0",
})


def _handle_slash_command(cmd: str, agent: Agent, ui: RageUI, console: Console) -> bool:
    """
    Handle slash commands. Returns True if command was handled.
    """
    original_cmd = cmd.strip()
    cmd = original_cmd.lower()

    if cmd in ("/help", "/h"):
        ui.print_help()
        return True

    elif cmd in ("/exit", "/quit", "/q"):
        console.print(f"\n  [bold #FF3D00]👋 RAGE BORN out. See you next time.[/bold #FF3D00]\n")
        sys.exit(0)

    elif cmd in ("/clear", "/cls"):
        os.system("clear" if os.name != "nt" else "cls")
        agent.llm.clear_history()
        console.print("  [dim]Chat history cleared.[/dim]")
        return True

    elif cmd == "/tasks":
        tasks = agent.task_manager.list_tasks()
        if tasks:
            ui.print_task_table(tasks)
        else:
            ui.print_info("No background tasks.")
        return True

    elif cmd == "/history":
        entries = agent.history.get_recent(20)
        if entries:
            ui.print_history_table(entries)
        else:
            ui.print_info("No history yet. Start using RAGE BORN!")
        return True

    elif cmd == "/memory":
        info = agent.memory.get_display_info()
        console.print(f"\n{info}\n")
        return True

    elif cmd == "/terminals":
        result = agent.tools.execute("list_terminals", {})
        console.print(f"\n{result.output}\n")
        return True

    elif cmd == "/config":
        from rage.config import load_config
        config = load_config()
        console.print("\n  [bold #FFB300]⚙ Configuration[/bold #FFB300]\n")
        for key, val in config.items():
            if key == "api_key" and val:
                display_val = val[:8] + "..." + val[-4:]  # Mask key
            else:
                display_val = val
            console.print(f"    [dim]{key}:[/dim] {display_val}")
        console.print()
        return True

    elif cmd.startswith("/remember "):
        fact = original_cmd[10:].strip()
        if fact:
            agent.memory.remember(fact)
            ui.print_success(f"Remembered: {fact}")
        return True

    elif cmd == "/browser":
        from rage.tools.browser import BrowserSession
        session = BrowserSession.get_instance()
        if session.is_running:
            tabs = session.list_tabs()
            console.print(f"\n{tabs}\n")
        else:
            console.print("\n  [dim]Browser is not running. Ask RAGE BORN to open a URL![/dim]\n")
        return True

    elif cmd.startswith("/browseurl "):
        url = original_cmd[11:].strip()
        if url:
            result = agent.tools.execute("browser_open", {"url": url})
            console.print(f"\n  {result.output}\n")
        return True

    elif cmd.startswith("/searchq "):
        query = original_cmd[9:].strip()
        if query:
            result = agent.tools.execute("browser_search", {"query": query})
            console.print(f"\n{result.output}\n")
        return True

    elif cmd == "/glogin":
        from rage.tools.browser import BrowserSession
        session = BrowserSession.get_instance()
        console.print("\n  [bold #FFB300]🔑 Google Workspace Login[/bold #FFB300]")
        console.print("  [dim]Opening browser in non-headless mode. Please log in to your Google account.[/dim]")
        console.print("  [dim]Once logged in, you can close the browser or type /browser to continue.[/dim]\n")
        
        if not session.is_running:
            session.launch(headless=False)
        session.navigate("https://accounts.google.com")
        return True

    elif cmd == "/plugins":
        from rage.tools.plugin import load_plugins
        console.print("\n  [bold #FFB300]🧩 Active Plugins[/bold #FFB300]")
        loaded = load_plugins(agent.tools)
        if loaded:
            for tool in loaded:
                console.print(f"  - [bold white]{tool}[/bold white]")
        else:
            console.print("  [dim]No custom plugins loaded from ~/.rage/plugins/[/dim]")
        console.print()
        return True

    elif cmd.startswith("/model"):
        parts = original_cmd.split()
        if len(parts) == 2:
            new_model = parts[1].strip()
            # Users often type /model <model_name> literally, strip the brackets
            if new_model.startswith("<") and new_model.endswith(">"):
                new_model = new_model[1:-1]
                
            from rage.config import load_config, save_config
            config = load_config()
            config["model"] = new_model
            save_config(config)
            agent.llm.model = new_model
            
            # Update API URL and Key based on model
            is_github_model = new_model.startswith(("openai/", "meta/"))
            is_groq_model = new_model.startswith("meta-llama/")
            is_nvidia_model = new_model.startswith(("z-ai/", "minimaxai/", "moonshotai/")) or new_model == "google/gemma-4-31b-it"
            
            if is_github_model:
                from rage.config import get_github_token
                agent.llm.api_key = get_github_token(config)
                agent.llm.api_url = config.get("github_api_url", "https://models.github.ai/inference/chat/completions")
            elif is_groq_model:
                from rage.config import get_groq_api_key
                agent.llm.api_key = get_groq_api_key(config)
                agent.llm.api_url = config.get("groq_api_url", "https://api.groq.com/openai/v1/chat/completions")
            elif is_nvidia_model:
                from rage.config import get_nvidia_api_key
                agent.llm.api_key = get_nvidia_api_key(config)
                agent.llm.api_url = config.get("nvidia_api_url", "https://integrate.api.nvidia.com/v1/chat/completions")
            else:
                from rage.config import get_api_key
                agent.llm.api_key = get_api_key(config)
                agent.llm.api_url = config.get("api_url", "https://lightning.ai/api/v1/chat/completions")
                
            ui.print_success(f"Model changed to: {new_model}")
        else:
            console.print("\n  [bold #FFB300]🤖 Model Selection[/bold #FFB300]")
            console.print(f"  Current model: [bold white]{agent.llm.model}[/bold white]")
            
            from prompt_toolkit.shortcuts import radiolist_dialog
            from rage.config import AVAILABLE_MODELS
            
            choices = [(m, m) for m in AVAILABLE_MODELS]
            
            # Find the index of the current model to set as default if possible
            # radiolist_dialog does not natively take a default index in older versions,
            # but we can just let it open. 
            
            new_model = radiolist_dialog(
                title="Model Selection",
                text="Use arrow keys to scroll, Space to select, and Enter to confirm.",
                values=choices,
                cancel_text="Cancel",
                ok_text="Select"
            ).run()
            
            if new_model:
                from rage.config import load_config, save_config
                config = load_config()
                config["model"] = new_model
                save_config(config)
                agent.llm.model = new_model
                
                # Update API URL and Key based on model
                is_github_model = new_model.startswith(("openai/", "meta/"))
                is_groq_model = new_model.startswith("meta-llama/")
                is_nvidia_model = new_model.startswith(("z-ai/", "minimaxai/", "moonshotai/")) or new_model == "google/gemma-4-31b-it"
                
                if is_github_model:
                    from rage.config import get_github_token
                    agent.llm.api_key = get_github_token(config)
                    agent.llm.api_url = config.get("github_api_url", "https://models.github.ai/inference/chat/completions")
                elif is_groq_model:
                    from rage.config import get_groq_api_key
                    agent.llm.api_key = get_groq_api_key(config)
                    agent.llm.api_url = config.get("groq_api_url", "https://api.groq.com/openai/v1/chat/completions")
                elif is_nvidia_model:
                    from rage.config import get_nvidia_api_key
                    agent.llm.api_key = get_nvidia_api_key(config)
                    agent.llm.api_url = config.get("nvidia_api_url", "https://integrate.api.nvidia.com/v1/chat/completions")
                else:
                    from rage.config import get_api_key
                    agent.llm.api_key = get_api_key(config)
                    agent.llm.api_url = config.get("api_url", "https://lightning.ai/api/v1/chat/completions")
                    
                ui.print_success(f"Model changed to: {new_model}")
            else:
                console.print("  [dim]Model selection cancelled.[/dim]")
        return True

    elif cmd.startswith("/plan ") or cmd == "/plan":
        raw_prompt = original_cmd[5:].strip() if len(original_cmd) > 5 else ""
        if not raw_prompt:
            console.print("  [dim]Usage: /plan <your idea>[/dim]")
            return True

        from rich.panel import Panel

        # -- Phase 1: Smart Prompt Generation --
        console.print(f"\n  [bold #FFB300]📋 Planning Mode[/bold #FFB300]")
        console.print(f"  [dim]Refining your prompt...[/dim]\n")

        refine_system = (
            "You are an expert software architect. The user will give you a rough idea. "
            "Rewrite it into a highly detailed, comprehensive software engineering requirement. "
            "Include specific technical details, file structure, and acceptance criteria. "
            "Output ONLY the refined requirement, nothing else."
        )
        # Save and restore conversation history so this one-shot doesn't pollute it
        saved_history = list(agent.llm.conversation_history)
        agent.llm.conversation_history = [{"role": "user", "content": raw_prompt}]
        smart_prompt = agent.llm.chat(refine_system, stream=False)
        agent.llm.conversation_history = saved_history  # Restore

        console.print(
            Panel(
                smart_prompt,
                border_style="#FFB300",
                title="[bold]📋 Refined Plan[/bold]",
                title_align="left",
                padding=(1, 2),
            )
        )

        # -- Phase 2: Feed master instruction to agent --
        master_instruction = (
            f"You are now in PLANNING MODE. Here is your detailed task:\n\n"
            f"---\n{smart_prompt}\n---\n\n"
            f"Follow these steps EXACTLY:\n"
            f"1. Use write_file to create 'implementation_plan.md' in the current directory with your technical approach.\n"
            f"2. Use write_file to create 'task.md' with a markdown checklist of all tasks using '- [ ] task description'.\n"
            f"3. Execute each task one by one using your tools.\n"
            f"4. After completing each task, use write_file (append=false) to update task.md, changing '[ ]' to '[x]' for completed items.\n"
            f"5. When ALL tasks are finished, respond with a final summary. Do NOT call any more tools after the summary.\n"
        )

        try:
            with ui.print_agent_thinking():
                agent.process_input_streaming(master_instruction)
        except KeyboardInterrupt:
            console.print("\n  [dim]Agent stopped.[/dim]")

        console.print(f"\n  [bold #00E676]✅ Plan execution complete.[/bold #00E676]\n")
        return True

    return False


def main():
    """Main entry point for RAGE BORN CLI."""
    import nest_asyncio
    nest_asyncio.apply()
    
    console = Console()
    ui = RageUI(console)

    # ── Handle direct command mode: rage "do something" ───────────────────
    direct_input = None
    if len(sys.argv) > 1:
        direct_input = " ".join(sys.argv[1:])

    # ── Load or create config ─────────────────────────────────────────────
    config = load_config()
    model_name = config.get("model", "lightning-ai/gemma-4-31B-it")
    is_github_model = model_name.startswith(("openai/", "meta/"))
    is_groq_model = model_name.startswith("meta-llama/")
    is_nvidia_model = model_name.startswith(("z-ai/", "minimaxai/", "moonshotai/")) or model_name == "google/gemma-4-31b-it"
    
    if is_github_model:
        api_key = get_github_token(config)
        api_url = config.get("github_api_url", "https://models.github.ai/inference/chat/completions")
    elif is_groq_model:
        api_key = get_groq_api_key(config)
        api_url = config.get("groq_api_url", "https://api.groq.com/openai/v1/chat/completions")
    elif is_nvidia_model:
        api_key = get_nvidia_api_key(config)
        api_url = config.get("nvidia_api_url", "https://integrate.api.nvidia.com/v1/chat/completions")
    else:
        api_key = get_api_key(config)
        api_url = config.get("api_url", "https://lightning.ai/api/v1/chat/completions")

    if not api_key:
        if direct_input:
            console.print("[bold red]Error:[/bold red] No API key configured. Run 'rage' to set up.")
            sys.exit(1)
        config = first_run_setup()
        model_name = config.get("model", "lightning-ai/gemma-4-31B-it")
        is_github_model = model_name.startswith(("openai/", "meta/"))
        is_groq_model = model_name.startswith("meta-llama/")
        is_nvidia_model = model_name.startswith(("z-ai/", "minimaxai/", "moonshotai/")) or model_name == "google/gemma-4-31b-it"
        if is_github_model:
            api_key = get_github_token(config)
            api_url = config.get("github_api_url", "https://models.github.ai/inference/chat/completions")
        elif is_groq_model:
            api_key = get_groq_api_key(config)
            api_url = config.get("groq_api_url", "https://api.groq.com/openai/v1/chat/completions")
        elif is_nvidia_model:
            api_key = get_nvidia_api_key(config)
            api_url = config.get("nvidia_api_url", "https://integrate.api.nvidia.com/v1/chat/completions")
        else:
            api_key = get_api_key(config)
            api_url = config.get("api_url", "https://lightning.ai/api/v1/chat/completions")
            
        if not api_key:
            console.print("[bold red]Error:[/bold red] API key is required. Set RAGE_API_KEY or run setup.")
            sys.exit(1)

    # ── Initialize components ─────────────────────────────────────────────
    llm = LLMClient(
        api_key=api_key,
        api_url=api_url,
        model=model_name,
        max_tokens=config.get("max_tokens", 4096),
        temperature=config.get("temperature", 0.7),
    )

    tools = create_default_registry()
    memory = Memory()
    history = History()
    task_manager = TaskManager()

    agent = Agent(
        llm=llm,
        tools=tools,
        memory=memory,
        history=history,
        task_manager=task_manager,
        ui=ui,
    )

    # Task completion callback
    def on_task_complete(task):
        status_icon = "✅" if task.status.value == "completed" else "❌"
        console.print(
            f"\n  {status_icon} [bold]Background Task #{task.id}[/bold] "
            f"[dim]{task.status.value}[/dim] — {task.command[:50]}"
        )

    task_manager.on_complete(on_task_complete)

    # ── Direct command mode ───────────────────────────────────────────────
    if direct_input:
        from rage.banner import print_compact_header
        print_compact_header(console)
        console.print(f"  [dim]>[/dim] {direct_input}\n")
        try:
            agent.process_input_streaming(direct_input)
        except KeyboardInterrupt:
            console.print("\n  [dim]Agent stopped.[/dim]")
        return

    # ── Interactive mode ──────────────────────────────────────────────────
    console.clear()
    print_banner(console, model=config.get("model", "gemma-4-31B-it"))

    # Setup prompt_toolkit
    ensure_rage_dirs()
    history_file = RAGE_DIR / "input_history"
    session = PromptSession(
        history=FileHistory(str(history_file)),
        style=PT_STYLE,
    )
    # ── Global Kill Switch (Ctrl+Alt+C) ───────────────────────────────────
    def _on_kill_hotkey():
        # Trigger KeyboardInterrupt in the main thread
        os.kill(os.getpid(), signal.SIGINT)

    try:
        from pynput import keyboard
        hotkey = keyboard.GlobalHotKeys({'<ctrl>+<alt>+c': _on_kill_hotkey})
        hotkey.start()
    except Exception as e:
        console.print(f"  [dim]Global kill switch (Ctrl+Alt+C) disabled: {e}[/dim]")

    # ── Main REPL Loop ────────────────────────────────────────────────────
    while True:
        try:
            user_input = session.prompt(
                HTML("<prompt>❯ </prompt>"),
                style=PT_STYLE,
            ).strip()

            if not user_input:
                continue

            # Handle slash commands
            if user_input.startswith("/"):
                if _handle_slash_command(user_input, agent, ui, console):
                    continue

            # Process through agent
            try:
                with ui.print_agent_thinking():
                    response = agent.process_input_streaming(user_input)
            except KeyboardInterrupt:
                console.print("\n  [dim]Agent stopped.[/dim]")
                continue

        except KeyboardInterrupt:
            console.print()  # New line after ^C
            continue
        except EOFError:
            console.print(f"\n  [bold #FF3D00]👋 RAGE BORN out.[/bold #FF3D00]\n")
            break
        except Exception as e:
            ui.print_error(f"Unexpected error: {e}")
            continue


if __name__ == "__main__":
    main()
