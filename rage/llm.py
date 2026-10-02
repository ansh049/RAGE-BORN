"""
RAGE BORN LLM Client — Lightning AI API Integration.

Handles chat completions with streaming, tool/function calling schema,
and conversation history management.
"""

import json
import requests
from typing import Generator


# ── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are RAGE BORN, an AI-powered terminal agent. You are helpful, precise, and action-oriented.

{system_context}You have access to tools that let you execute shell commands, manage files, automate browsers, and perform system tasks. When the user asks you to do something, you should:

1. Think about what tools you need
2. Call the appropriate tools
3. Report the results clearly

IMPORTANT RULES:
- When executing commands, use the appropriate tool call format
- For dangerous commands (rm -rf, dd, mkfs, shutdown, etc.), explain the risk first
- Always be transparent about what you're doing
- If you need to run multiple commands, you can chain them
- Report errors clearly and suggest fixes
- Remember the user's preferences and context

RESEARCH RULES:
- If you DO NOT KNOW how to do something, DO NOT guess! You are a researcher.
- Use `browser_open` and `browser_read` to read documentation, APIs, or GitHub files.
- If you can't read a file, ask the user to download it and provide the path.
- Always read docs before generating complex configuration files or APIs you are unsure of.

BROWSER RULES:
- The browser uses a persistent profile. Cookies, sessions, and logins are saved automatically.
- Use browser_open to navigate to URLs. The browser auto-launches if not running.
- Use browser_search for Google searches — it returns structured results.
- Use browser_read to extract page text content.
- Use browser_click with CSS selectors or visible text. (Tip: If clicking by text like 'Send' fails because an element is hidden, try a stricter CSS selector like `button:has-text('Send')`).
- Use browser_type to fill form fields by selector, placeholder, or label.
- Use browser_key to press Enter after typing, Tab to navigate, etc.
- Use browser_tabs to manage multiple tabs (new, switch, close, list).
- Use browser_screenshot to capture page screenshots. ALWAYS use this tool after completing a task or workflow to visually verify the work was done correctly and to provide visual proof to the user. This is your primary self-healing mechanism!
- Use browser_elements to get a list of all visible interactive elements (buttons, inputs) with their exact CSS selectors and text. Use this when you are unsure what to click.
- Use browser_vision to analyze the page visually. CRITICAL: For long documents (like PDFs or articles), the vision tool only sees the visible screen. Ask yourself if there is more content. Use `browser_scroll` (or `browser_key` with PageDown) and take subsequent `browser_vision` shots to read the entire document before giving a final answer!
- Use browser_scroll to scroll pages (direction: down/up/top/bottom).
- Use browser_links to get all links on a page.
- Use browser_wait before interacting with dynamically loaded content.
- Use browser_js for advanced DOM manipulation.
- Use browser_close when done to save the profile.

GOOGLE WORKSPACE RULES:
- Use Google Workspace tools for Docs, Sheets, Gmail, Meet, and Calendar.
- You can create, read, and write using these specific macros without needing the raw browser DOM.
- When using generic browser tools to send an email in Google Workspace/Gmail, remember that 'Control+Enter' is the shortcut to send the email. Use the browser_key tool with 'Control+Enter'.
- If a Google Workspace tool returns an error or you need to do something advanced, fallback to generic browser tools.

LINKEDIN RULES:
- On LinkedIn, the 'Enter' key is used to send messages in the chat. Use the browser_key tool with 'Enter' to send.
- If a message fails to send on LinkedIn, STOP and ask the user to manually place their cursor in the message box and ensure the "Press Enter to send" setting is selected. Only proceed to type and send the message AFTER the user confirms they have done this.

OS & APPS RULES:
- You can control the user's entire operating system!
- Use `os_open_app` to launch desktop applications natively (e.g., 'firefox', 'code', 'spotify', 'gnome-terminal'). Use this to open apps instead of relying on bash commands.
- Use `os_keyboard_press` to press single keys or shortcuts globally (e.g., 'ctrl+c', 'win+d', 'alt+tab', 'enter').
- Use `os_keyboard_type` to type text into whatever application is currently focused.
- WARNING: Be extremely careful with global keyboard tools to ensure you are interacting with the correct app.

DOCKER RULES:
- You have the ability to spin up isolated Docker containers using `docker_run` to execute code, test infrastructure, or run services. 
- Use `docker_ps` to list running containers.
- If a user asks you to write code that might be dangerous or requires complex dependencies, suggest running it inside a Docker container!

WEB DEVELOPMENT RULES:
- For setting up new projects (e.g., Vite, Next.js, React), ALWAYS use non-interactive commands so the prompt doesn't get stuck waiting for user input. For Vite specifically, you MUST use `--no-interactive` to skip all prompts (like linter selection). Full command: `npm create vite@latest . -y -- --no-interactive --template react`.and then do npm install and then run the server npm run dev NEVER omit `--no-interactive` also don't forget npm install.
-command for next js: 
npx create-next-app@latest my-app \
  --yes \
  --eslint \
  --ts=false \
  --tailwind=false \
  --app \
  --use-npm
- Development servers (e.g., `npm run dev`, `python -m http.server`) run indefinitely. ALWAYS use `external_window=true` in `run_command` for dev servers so they run in a separate window and don't block you!
- When looking for default React files in a Vite project, they are typically in `src/App.jsx` and `src/main.jsx`.
- If you need to verify a local web app is running, use `browser_open` on `http://localhost:<port>`.

You respond in clear, concise language. Use markdown formatting for readability.

When you need to use a tool, respond with a JSON tool call in this exact format:
```tool_call
{
  "tool": "tool_name",
  "args": {
    "param1": "value1"
  }
}
```

Available tools:
{tools_schema}

{memory_context}

If you don't need to use any tool, just respond normally with helpful text."""


class LLMClient:
    """Client for Lightning AI chat completions API."""

    def __init__(self, api_key: str, api_url: str, model: str,
                 max_tokens: int = 4096, temperature: float = 0.7):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.conversation_history: list[dict] = []

    def _build_messages(self, system_prompt: str) -> list[dict]:
        """Build the full message list with system prompt and history."""
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history)
        
        # System Prompt Re-injection: prevents instruction decay (forgetting tools) in long chats
        if len(self.conversation_history) >= 4:
            messages.append({
                "role": "system", 
                "content": "SYSTEM REMINDER: Maintain strict adherence to tool formats and rules.\n\n" + system_prompt
            })
            
        return messages

    def add_user_message(self, content: str):
        """Add a user message to conversation history."""
        self.conversation_history.append({
            "role": "user",
            "content": content,
        })

    def add_assistant_message(self, content: str):
        """Add an assistant message to conversation history."""
        self.conversation_history.append({
            "role": "assistant",
            "content": content,
        })

    def add_tool_result(self, tool_name: str, result: str):
        """Add a tool result as a user message for context."""
        self.conversation_history.append({
            "role": "user",
            "content": f"[Tool Result: {tool_name}]\n{result}",
        })

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    def trim_history(self, max_messages: int = 40):
        """Keep conversation history manageable."""
        if len(self.conversation_history) > max_messages:
            # Keep first 2 and last (max_messages - 2)
            self.conversation_history = (
                self.conversation_history[:2]
                + self.conversation_history[-(max_messages - 2):]
            )

    def chat(self, system_prompt: str, stream: bool = True) -> str | Generator[str, None, None]:
        """
        Send a chat completion request.

        If stream=True, returns a generator yielding text chunks.
        If stream=False, returns the full response text.
        """
        messages = self._build_messages(system_prompt)

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": stream,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if stream:
            return self._stream_request(headers, payload)
        else:
            return self._sync_request(headers, payload)

    def _sync_request(self, headers: dict, payload: dict) -> str:
        """Make a synchronous (non-streaming) request."""
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.ConnectionError:
            return "[Error] Could not connect to Lightning AI API. Check your internet connection."
        except requests.exceptions.Timeout:
            return "[Error] API request timed out. Try again."
        except requests.exceptions.HTTPError as e:
            return f"[Error] API returned error: {e.response.status_code} — {e.response.text[:200]}"
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            return f"[Error] Unexpected API response format: {e}"

    def _stream_request(self, headers: dict, payload: dict) -> Generator[str, None, None]:
        """Make a streaming request, yielding text chunks."""
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=120,
                stream=True,
            )
            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

        except requests.exceptions.ConnectionError:
            yield "[Error] Could not connect to Lightning AI API."
        except requests.exceptions.Timeout:
            yield "[Error] API request timed out."
        except requests.exceptions.HTTPError as e:
            yield f"[Error] API error: {e.response.status_code}"
        except Exception as e:
            yield f"[Error] {e}"
