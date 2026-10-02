"""
RAGE Google Workspace Macro Tools.

Provides high-level automation for Google Workspace using the persistent Playwright browser.
This avoids the need for OAuth API setup by driving the browser exactly like a user.
"""

import time
from rage.tools.base import BaseTool, ToolResult
from rage.tools.browser import BrowserSession


class GWorkspaceDocsTool(BaseTool):
    """Automate Google Docs."""
    name = "gworkspace_docs"
    description = (
        "Automate Google Docs. Actions: 'create' (opens docs.new), "
        "'read' (extracts text from current doc), 'write' (types text into current doc)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Action to perform: 'create', 'read', 'write'",
            },
            "text": {
                "type": "string",
                "description": "Text to write (required for 'write' action)",
            },
        },
        "required": ["action"],
    }

    def execute(self, action: str, text: str = None) -> ToolResult:
        session = BrowserSession.get_instance()
        if not session.is_running and action != "create":
            return ToolResult(success=False, output="", error="Browser not running.")

        if action == "create":
            if not session.is_running:
                session.launch(headless=False)
            res = session.navigate("https://docs.new")
            session.wait_for("div.kix-appview-editor", timeout=15000)
            return ToolResult(success=True, output=f"New Google Doc created.\n{res}")

        elif action == "read":
            res = session.get_text("div.kix-appview-editor")
            return ToolResult(success=True, output=f"Doc Content:\n{res}")

        elif action == "write":
            if not text:
                return ToolResult(success=False, output="", error="Text is required for write.")
            page = session._get_page()
            page.bring_to_front()
            # Click the editor to focus (force center click on the canvas)
            try:
                page.click(".kix-canvas-tile-content", force=True, timeout=2000)
            except:
                page.click("div.kix-appview-editor", force=True)
            
            time.sleep(1)
            # Type text character by character for reliability
            page.keyboard.type(text, delay=2)
            return ToolResult(success=True, output="Text written to document.")

        return ToolResult(success=False, output="", error="Unknown action.")


class GWorkspaceSheetsTool(BaseTool):
    """Automate Google Sheets."""
    name = "gworkspace_sheets"
    description = (
        "Automate Google Sheets. Actions: 'create' (opens sheets.new), 'read' (extracts grid data)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Action: 'create' or 'read'",
            },
        },
        "required": ["action"],
    }

    def execute(self, action: str) -> ToolResult:
        session = BrowserSession.get_instance()
        if not session.is_running and action != "create":
            return ToolResult(success=False, output="", error="Browser not running.")

        if action == "create":
            if not session.is_running:
                session.launch(headless=False)
            res = session.navigate("https://sheets.new")
            session.wait_for("div#waffle-grid-container", timeout=15000)
            return ToolResult(success=True, output=f"New Google Sheet created.\n{res}")

        elif action == "read":
            # Extract text from the active sheet cells
            res = session.get_text("div.grid-container")
            return ToolResult(success=True, output=f"Sheet Content (visible cells):\n{res}")

        return ToolResult(success=False, output="", error="Unknown action.")


class GWorkspaceGmailTool(BaseTool):
    """Automate Gmail."""
    name = "gworkspace_gmail"
    description = (
        "Automate Gmail. Actions: 'compose' (opens compose window), "
        "'read_inbox' (reads recent emails)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Action: 'compose', 'read_inbox'",
            },
            "to": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"},
        },
        "required": ["action"],
    }

    def execute(self, action: str, to: str = "", subject: str = "", body: str = "") -> ToolResult:
        session = BrowserSession.get_instance()
        if not session.is_running:
            session.launch(headless=False)

        if action == "compose":
            url = "https://mail.google.com/mail/u/0/#compose"
            session.navigate(url)
            session.wait_for("div[role='dialog']", timeout=15000)
            
            if to:
                page = session._get_page()
                try:
                    # Gmail 'To' field uses dynamic IDs. Try multiple common attributes.
                    page.fill("input[aria-label='To recipients'], input[peoplekit-id], input.agP", to, timeout=5000)
                except Exception:
                    # Fallback: When Compose opens, the 'To' field is focused by default
                    page.keyboard.type(to, delay=10)
                page.keyboard.press("Enter")
            if subject:
                session.type_text("input[name='subjectbox']", subject)
            if body:
                session.type_text("div[aria-label='Message Body']", body)
            
            return ToolResult(success=True, output="Compose window opened and filled. Use browser_click on 'Send' to send.")

        elif action == "read_inbox":
            session.navigate("https://mail.google.com/mail/u/0/#inbox")
            session.wait_for("div[role='main']", timeout=15000)
            res = session.get_text("div[role='main']", max_length=3000)
            return ToolResult(success=True, output=f"Inbox Content:\n{res}")

        return ToolResult(success=False, output="", error="Unknown action.")


class GWorkspaceMeetTool(BaseTool):
    """Automate Google Meet."""
    name = "gworkspace_meet"
    description = (
        "Automate Google Meet. Actions: 'create' (meet.new to start a meeting and get link)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Action: 'create'",
            },
        },
        "required": ["action"],
    }

    def execute(self, action: str) -> ToolResult:
        session = BrowserSession.get_instance()
        
        if action == "create":
            if not session.is_running:
                session.launch(headless=False)
            session.navigate("https://meet.new")
            # Wait for meeting to initialize and URL to update from meet.new to meet.google.com/xxx-xxxx-xxx
            time.sleep(5) 
            page = session._get_page()
            url = page.url
            return ToolResult(success=True, output=f"Meeting started. Link: {url}")

        return ToolResult(success=False, output="", error="Unknown action.")


class GWorkspaceCalendarTool(BaseTool):
    """Automate Google Calendar."""
    name = "gworkspace_calendar"
    description = (
        "Automate Google Calendar. Actions: 'agenda' (view today's schedule), 'create' (cal.new to schedule)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Action: 'agenda', 'create'",
            },
        },
        "required": ["action"],
    }

    def execute(self, action: str) -> ToolResult:
        session = BrowserSession.get_instance()
        if not session.is_running:
            session.launch(headless=False)

        if action == "agenda":
            session.navigate("https://calendar.google.com/calendar/u/0/r/agenda")
            session.wait_for("div[role='main']", timeout=15000)
            res = session.get_text("div[role='main']", max_length=3000)
            return ToolResult(success=True, output=f"Today's Agenda:\n{res}")

        elif action == "create":
            session.navigate("https://cal.new")
            session.wait_for("input[aria-label='Title']", timeout=15000)
            return ToolResult(success=True, output="Calendar event creation page opened. Use browser_type and browser_click to fill details and save.")

        return ToolResult(success=False, output="", error="Unknown action.")
