# RAGE BORN: The Ultimate Autonomous Terminal Agent

Welcome to the official documentation for **RAGE BORN**, a highly advanced, model-agnostic, AI-powered terminal agent. Designed for developers, researchers, and power users, RAGE BORN transcends the limitations of traditional AI coding assistants by providing autonomous control over your entire operating system, browser, and cloud workspace.

---

## 📑 Table of Contents

1. [Introduction & Philosophy](#1-introduction--philosophy)
2. [Why RAGE BORN over Alternatives?](#2-why-rage-born-over-alternatives)
3. [Core Capabilities](#3-core-capabilities)
    - [Full OS & Terminal Control](#full-os--terminal-control)
    - [Autonomous File Management & Coding](#autonomous-file-management--coding)
    - [Persistent Browser Automation](#persistent-browser-automation)
    - [Google Workspace & Cloud Integration](#google-workspace--cloud-integration)
    - [Multimodal Vision & Image Parsing](#multimodal-vision--image-parsing)
4. [Supported Models & Economics](#4-supported-models--economics)
5. [How It Works Under the Hood](#5-how-it-works-under-the-hood)

---

## 1. Introduction & Philosophy

RAGE BORN is not just an autocomplete tool or a basic chat interface. It is an **agentic loop** that lives in your terminal. You assign it a task, and it autonomously researches, navigates, executes, and verifies its own work until the goal is achieved. 

Whether you need to debug a complex Linux server issue, automate sending messages on LinkedIn, write a document in Google Docs, or refactor an entire codebase, RAGE BORN acts as your autonomous co-pilot.

---

## 2. Why RAGE BORN over Alternatives?

While tools like *Claude Code* offer great coding assistance, they suffer from strict vendor lock-in, limited scopes, and high costs. RAGE BORN shatters these boundaries:

* **Model Agnostic**: You are not locked into a single provider. Switch seamlessly between OpenAI, Anthropic, Lightning AI, and open-source models based on your task and budget.
* **Total System Access**: It doesn't just read code; it can control your entire OS, run arbitrary terminal commands, manage Docker containers, and manipulate file systems.
* **Persistent Web Browsing**: Unlike sandboxed AI browsers that forget who you are, RAGE BORN uses a persistent local profile. Once you log into LinkedIn, Gmail, or X (Twitter), it stays logged in forever, ready to automate your personal accounts on your behalf.
* **Cost Efficiency**: By allowing the use of highly optimized open-source models (like Gemma), running RAGE BORN is absurdly cheap compared to proprietary APIs.

---

## 3. Core Capabilities

### Full OS & Terminal Control
RAGE BORN has native access to your Linux terminal. It can run commands, install dependencies, compile code, and debug errors. If a build fails, it reads the traceback, modifies the code, and recompiles entirely on its own.

### Autonomous File Management & Coding
It can navigate your file system, read vast codebases, and use targeted code-editing tools to surgically modify files. From creating complex project structures to patching minute syntax errors, it handles the entire software development lifecycle.

### Persistent Browser Automation
Using advanced Playwright integration, RAGE BORN can:
* Open URLs and search the web (bypassing captchas via specialized tools).
* Discover interactive elements in the DOM dynamically.
* Type, click, and navigate across complex web apps.
* Automate personal messaging (e.g., searching for a connection on LinkedIn and sending a direct message).

### Google Workspace & Cloud Integration
RAGE BORN comes with native, highly-reliable `gworkspace_*` tools. It can autonomously create and write content directly into **Google Docs**, pull data from **Google Sheets**, read your **Gmail**, and manage your **Calendar**—all without you lifting a finger.

### Multimodal Vision & Image Parsing
RAGE BORN isn't blind. Through the `browser_vision` and `browser_screenshot` tools, the agent takes actual screenshots of what it is doing. It can pass these images back to vision-capable models to verify UI layouts, parse un-selectable text, and double-check its own automated work (self-healing).

---

## 4. Supported Models & Economics

RAGE BORN supports a wide array of models through flexible API integrations (including OpenAI, Anthropic, and Lightning AI OSS models). 

**The Power of Gemma-4-31B-it**
One of the most powerful and cost-effective engines for RAGE BORN is **Gemma-4-31B-it**. This model excels at agentic tasks, reasoning, and tool calling, while being incredibly affordable:

* **Input Cost**: ~$0.14 per 1,000,000 tokens
* **Output Cost**: ~$0.40 per 1,000,000 tokens
* **Context Window**: 128,000 tokens

At this price point, you can leave RAGE BORN running in complex, multi-step loops (reading entire codebases or browsing long web pages) for fractions of a penny. Furthermore, when paired with vision tools, models like this can parse images and deeply understand visual context to course-correct on the fly.

---

## 5. How It Works Under the Hood

1. **The Loop**: You provide a natural language prompt in the terminal.
2. **Tool Selection**: The LLM analyzes the prompt and outputs a strict JSON tool schema specifying which tool to invoke.
3. **Execution**: The RAGE BORN runtime intercepts the JSON, executes the local tool (e.g., typing into a browser, running a bash command, creating a file), and captures the output.
4. **Self-Healing & Verification**: The output (or a screenshot) is fed back to the model. If an error occurs (e.g., element not found, syntax error), the model recognizes the failure, adjusts its strategy, and tries again.
5. **Completion**: The agent returns control to you once it successfully verifies the goal is complete.

---
*Generated by RAGE BORN.*
