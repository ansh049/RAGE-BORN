# Connect to Any LLMs API

RAGE's architecture separates the planner and the tools, allowing it to connect to state-of-the-art Large Language Models (LLMs).

## Integration Details
- **Bring Your Own API Key**: On the first run, RAGE asks for your Lightning AI API key (or other supported providers). You can set it via the `RAGE_API_KEY` environment variable.
- **Model Switching**: Use the `/model` command to select different AI models according to your needs. This flexibility means you can utilize various models (like Claude, Gemini, or Llama) for different tasks.
- **Persistent Memory**: The connected LLM has access to persistent memory and task history, meaning it remembers your context and preferences across multiple sessions.
