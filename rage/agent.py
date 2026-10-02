"""
RAGE BORN Agent — Core AI Agent Loop.

Orchestrates the conversation between user, LLM, and tools.
Handles tool call parsing, multi-step reasoning, and error recovery.
"""

import json
import re
from rage.llm import LLMClient, SYSTEM_PROMPT
from rage.tools.registry import ToolRegistry
from rage.memory import Memory
from rage.history import History
from rage.tasks.manager import TaskManager
from rage.ui import RageUI


class Agent:
    """Core RAGE agent that connects user input to LLM and tools."""

    def __init__(
        self,
        llm: LLMClient,
        tools: ToolRegistry,
        memory: Memory,
        history: History,
        task_manager: TaskManager,
        ui: RageUI,
    ):
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.history = history
        self.task_manager = task_manager
        self.ui = ui
        self.max_tool_iterations = 30  # Prevent infinite loops but allow long web tasks

    def _build_system_prompt(self) -> str:
        """Build the system prompt with tools and memory context."""
        tools_desc = self.tools.get_tools_description()
        memory_ctx = self.memory.get_context_string()
        
        from rage.system import get_system_info
        info = get_system_info()
        sys_ctx = (
            f"OS: {info.get('os')}\n"
            f"Distro: {info.get('distro')}\n"
            f"Kernel: {info.get('kernel')}\n"
            f"Shell: {info.get('shell')}\n"
            f"Memory: {info.get('mem')}\n"
            f"User: {info.get('user')}\n"
            f"Hostname: {info.get('hostname')}\n\n"
        )

        return SYSTEM_PROMPT.replace(
            "{tools_schema}", tools_desc
        ).replace(
            "{memory_context}",
            f"User Context & Memory:\n{memory_ctx}" if memory_ctx else "",
        ).replace(
            "{system_context}",
            f"Current System Context:\n{sys_ctx}",
        )

    def process_input(self, user_input: str) -> str:
        """
        Process user input through the full agent loop:
        1. Send to LLM with tools context
        2. Parse response for tool calls
        3. Execute tools
        4. Feed results back to LLM
        5. Return final response
        """
        # Add user message to LLM history
        self.llm.add_user_message(user_input)
        self.llm.trim_history()

        system_prompt = self._build_system_prompt()

        # Agent loop — LLM may call tools multiple times
        for iteration in range(self.max_tool_iterations):
            # Get LLM response (non-streaming for tool parsing)
            response = self.llm.chat(system_prompt, stream=False)

            # Check for tool calls
            tool_calls = self._extract_tool_calls(response)

            if not tool_calls:
                # No tool calls — this is the final response
                self.llm.add_assistant_message(response)
                self._try_extract_memory(user_input, response)
                return response

            # Execute tool calls
            results_text = []
            for tool_call in tool_calls:
                tool_name = tool_call.get("tool", "")
                args = tool_call.get("args", {})

                self.ui.print_tool_call(tool_name, args)

                # Execute tool
                if tool_name == "system_clear_context":
                    self.llm.clear_history()
                    self.llm.add_user_message(user_input) # Keep current context
                    from rage.tools.base import ToolResult
                    result = ToolResult(success=True, output="Conversation history has been wiped clean. You have a fresh slate.")
                else:
                    result = self.tools.execute(tool_name, args)

                self.ui.print_tool_result(tool_name, str(result), result.success)

                # Log to history
                self.history.add(
                    command=f"{tool_name}({json.dumps(args)[:100]})",
                    output=str(result)[:500],
                    success=result.success,
                    duration=result.data.get("duration", ""),
                    error=result.error,
                    tool_name=tool_name,
                )

                results_text.append(
                    f"[{tool_name}] {'Success' if result.success else 'Failed'}: {str(result)}"
                )

            # Feed results back to LLM
            combined_results = "\n".join(results_text)
            # Add assistant message with tool calls, then tool results
            clean_response = self._strip_tool_calls(response)
            if clean_response.strip():
                self.llm.add_assistant_message(clean_response)
            self.llm.add_tool_result("tools", combined_results)

        # If we hit max iterations, return what we have
        return "[RAGE BORN reached maximum tool iterations. Here's what was accomplished so far.]"

    def process_input_streaming(self, user_input: str) -> str:
        """
        Process user input with streaming response for the final output.
        Uses non-streaming for tool calls, then streams the final answer.
        """
        # Add user message to LLM history
        self.llm.add_user_message(user_input)
        self.llm.trim_history()

        system_prompt = self._build_system_prompt()

        # Agent loop
        for iteration in range(self.max_tool_iterations):
            # First, try non-streaming to detect tool calls
            response = self.llm.chat(system_prompt, stream=False)

            tool_calls = self._extract_tool_calls(response)

            if not tool_calls:
                # No tool calls — this is the final response
                # Stream it to the user
                self.llm.add_assistant_message(response)
                self._try_extract_memory(user_input, response)
                self.ui.print_agent_response(response)
                return response

            # Execute tool calls (same as non-streaming)
            results_text = []
            for tool_call in tool_calls:
                tool_name = tool_call.get("tool", "")
                args = tool_call.get("args", {})

                self.ui.print_tool_call(tool_name, args)
                if tool_name == "system_clear_context":
                    self.llm.clear_history()
                    self.llm.add_user_message(user_input)
                    from rage.tools.base import ToolResult
                    result = ToolResult(success=True, output="Conversation history has been wiped clean. You have a fresh slate.")
                else:
                    result = self.tools.execute(tool_name, args)
                self.ui.print_tool_result(tool_name, str(result), result.success)

                self.history.add(
                    command=f"{tool_name}({json.dumps(args)[:100]})",
                    output=str(result)[:500],
                    success=result.success,
                    duration=result.data.get("duration", ""),
                    error=result.error,
                    tool_name=tool_name,
                )

                results_text.append(
                    f"[{tool_name}] {'Success' if result.success else 'Failed'}: {str(result)}"
                )

            combined_results = "\n".join(results_text)
            clean_response = self._strip_tool_calls(response)
            if clean_response.strip():
                self.llm.add_assistant_message(clean_response)
            self.llm.add_tool_result("tools", combined_results)

        final = "[RAGE BORN reached maximum tool iterations.]"
        self.ui.print_agent_response(final)
        return final

    def _extract_tool_calls(self, response: str) -> list[dict]:
        """Extract tool calls from LLM response."""
        tool_calls = []

        # Pattern: ```tool_call\n{json}\n```
        pattern = r"```tool_call\s*\n(.*?)\n```"
        matches = re.findall(pattern, response, re.DOTALL)

        for match in matches:
            try:
                data = json.loads(match.strip())
                if "tool" in data:
                    tool_calls.append(data)
            except json.JSONDecodeError:
                continue

        # Also try to find JSON objects with "tool" key directly
        # (in case LLM doesn't use the code block format exactly)
        if not tool_calls:
            json_pattern = r'\{[^{}]*"tool"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\{[^{}]*\}[^{}]*\}'
            json_matches = re.findall(json_pattern, response, re.DOTALL)
            for match in json_matches:
                try:
                    data = json.loads(match)
                    if "tool" in data:
                        tool_calls.append(data)
                except json.JSONDecodeError:
                    continue

        # Also support alternative call:tool_name {...} syntax (common model hallucination)
        if not tool_calls:
            alt_pattern = r'call:([a-zA-Z0-9_]+)\s*(\{.*?\})'
            alt_matches = re.findall(alt_pattern, response, re.DOTALL)
            for tool_name, args_str in alt_matches:
                args = {}
                try:
                    if args_str.strip() != "{}":
                        args = json.loads(args_str)
                except json.JSONDecodeError:
                    pass
                
                # Handle nested hallucination: call:tool_call { "tool": "x", "args": {} }
                if tool_name == "tool_call" and "tool" in args:
                    tool_calls.append({"tool": args["tool"], "args": args.get("args", {})})
                else:
                    tool_calls.append({"tool": tool_name, "args": args})

        # Handle minimax-specific hallucination: minimax:tool_call <tool_call> ... </tool_call>
        if not tool_calls:
            minimax_pattern = r'<\s*tool_call\s*>(.*?)</\s*tool_call\s*>'
            minimax_matches = re.findall(minimax_pattern, response, re.DOTALL)
            for match in minimax_matches:
                try:
                    data = json.loads(match.strip())
                    if "tool" in data:
                        tool_calls.append(data)
                    else:
                        # Sometimes minimax outputs just the tool object properties directly without the wrapper
                        # e.g. <tool_call>{"name": "browser_elements", "arguments": {}}</tool_call>
                        if "name" in data and "arguments" in data:
                            tool_calls.append({"tool": data["name"], "args": data["arguments"]})
                except json.JSONDecodeError:
                    continue

        return tool_calls

    def _strip_tool_calls(self, response: str) -> str:
        """Remove tool call blocks from a response to get the conversational text."""
        # Remove ```tool_call...``` blocks
        cleaned = re.sub(r"```tool_call\s*\n.*?\n```", "", response, flags=re.DOTALL)
        # Remove inline JSON tool calls
        cleaned = re.sub(
            r'\{[^{}]*"tool"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\{[^{}]*\}[^{}]*\}',
            "", cleaned, flags=re.DOTALL,
        )
        # Remove alternative call syntax and tokens
        cleaned = re.sub(r'<\|tool_call\|>.*?<\|/tool_call\|>', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'<\s*tool_call\s*>.*?</\s*tool_call\s*>', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'minimax:tool_call', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'[a-zA-Z0-9_]+:tool_call\s*<\s*tool_call\s*>.*?</\s*tool_call\s*>', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'<\|tool_call>.*?<tool_call\|>', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'call:[a-zA-Z0-9_]+\s*\{.*?\}', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'<\|tool_call\|>.*?<tool_call\|>', '', cleaned, flags=re.DOTALL)
        
        return cleaned.strip()

    def _try_extract_memory(self, user_input: str, response: str):
        """
        Try to extract useful information to remember from the conversation.
        Simple heuristic-based extraction.
        """
        lowered = user_input.lower()

        # Detect preferences
        pref_patterns = {
            "editor": ["prefer", "use", "like"],
            "shell": ["prefer", "use", "my shell"],
            "language": ["favorite language", "prefer", "mainly use"],
        }
        for category, keywords in pref_patterns.items():
            for kw in keywords:
                if kw in lowered and category in lowered:
                    # Simple extraction - store the user's statement
                    self.memory.remember(f"User said about {category}: {user_input[:200]}")
                    return

        # Detect explicit "remember" requests
        if "remember" in lowered:
            self.memory.remember(user_input[:200])
