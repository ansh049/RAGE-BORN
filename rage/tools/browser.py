"""
RAGE Browser Tool — Playwright-based Browser Automation.

Provides persistent-profile browser automation with:
- Page navigation, clicking, typing, scrolling
- Multi-tab management
- Screenshot capture
- Page content extraction / summarization
- Google search shortcut
- Form filling and file downloads
- Persistent cookies/sessions/logins across sessions

Uses ~/.rage/browser_profile/ for persistent browser data.
"""

import os
import json
import time
from pathlib import Path
from rage.tools.base import BaseTool, ToolResult
from rage.config import BROWSER_PROFILE_DIR, RAGE_DIR, ensure_rage_dirs


# ── Browser Session Manager ──────────────────────────────────────────────────

class BrowserSession:
    """
    Manages a persistent Playwright browser session.

    Uses a persistent Chromium context so cookies, logins, sessions,
    bookmarks, history, and downloads are all retained across restarts.
    """

    _instance = None

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._context = None
        self._pages: dict[str, object] = {}  # tab_name -> Page
        self._active_tab: str = "main"
        self._headless: bool = False
        self._downloads_dir = str(RAGE_DIR / "downloads")

    @classmethod
    def get_instance(cls) -> "BrowserSession":
        """Singleton access to the browser session."""
        if cls._instance is None:
            cls._instance = BrowserSession()
        return cls._instance

    @property
    def is_running(self) -> bool:
        if self._context is None:
            return False
        try:
            # If the context is closed, accessing pages usually throws or is empty
            if not self._context.pages and self._pages:
                self._cleanup()
                return False
            return True
        except Exception:
            self._cleanup()
            return False

    def _ensure_dirs(self):
        """Ensure browser directories exist."""
        ensure_rage_dirs()
        os.makedirs(self._downloads_dir, exist_ok=True)
        os.makedirs(str(BROWSER_PROFILE_DIR), exist_ok=True)

    def launch(self, headless: bool = False) -> str:
        """Launch browser with persistent profile."""
        if self.is_running:
            return "Browser is already running."

        self._headless = headless
        self._ensure_dirs()

        try:
            from playwright.sync_api import sync_playwright
            import subprocess
            import time

            self._playwright = sync_playwright().start()

            # Try to connect to an existing detached browser session first
            try:
                self._browser = self._playwright.chromium.connect_over_cdp("http://localhost:9222")
                self._context = self._browser.contexts[0] if self._browser.contexts else self._browser.new_context()
            except Exception:
                # Launch a new detached browser process
                exe = self._playwright.chromium.executable_path
                cmd = [
                    exe,
                    "--remote-debugging-port=9222",
                    f"--user-data-dir={BROWSER_PROFILE_DIR}",
                    "--no-sandbox",
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                ]
                if headless:
                    cmd.append("--headless")
                    
                self._browser_process = subprocess.Popen(cmd, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Wait for the browser to start
                connected = False
                for _ in range(20):
                    time.sleep(0.5)
                    try:
                        self._browser = self._playwright.chromium.connect_over_cdp("http://localhost:9222")
                        self._context = self._browser.contexts[0] if self._browser.contexts else self._browser.new_context()
                        connected = True
                        break
                    except Exception:
                        pass
                        
                if not connected:
                    raise Exception("Failed to connect to the detached browser process.")

            # Set download path
            # The first page is auto-created by persistent context
            if self._context.pages:
                self._pages["main"] = self._context.pages[0]
            else:
                self._pages["main"] = self._context.new_page()

            self._active_tab = "main"

            return "Browser launched with persistent profile."

        except ImportError:
            return (
                "Error: Playwright is not installed. "
                "Run: pip install playwright && playwright install chromium"
            )
        except Exception as e:
            self._cleanup()
            return f"Error launching browser: {e}"

    def close(self) -> str:
        """Close the browser, preserving the profile."""
        if not self.is_running:
            return "Browser is not running."

        try:
            self._cleanup()
            return "Browser closed. Profile saved."
        except Exception as e:
            return f"Error closing browser: {e}"

    def _cleanup(self):
        """Clean up browser resources."""
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        self._context = None
        self._browser = None
        self._playwright = None
        self._pages = {}
        self._active_tab = "main"

    def _get_page(self, tab_name: str = None, create_if_missing: bool = False):
        """Get the page for a given tab, or the active tab."""
        # Handle common LLM hallucination where it copies the (default: active tab) text literally
        if tab_name in ("active tab", "active_tab", "active"):
            tab_name = None
            
        name = tab_name or self._active_tab
        page = self._pages.get(name)
        if page is None:
            raise ValueError(
                f"Tab '{name}' not found. "
                f"Available tabs: {', '.join(self._pages.keys())}"
            )
        
        try:
            if page.is_closed():
                # If active tab is closed, try to use any available page
                if self._context and self._context.pages:
                    self._pages[name] = self._context.pages[0]
                    return self._pages[name]
                else:
                    self._cleanup()
                    raise RuntimeError("Browser window was closed by the user.")
        except Exception as e:
            if "has been closed" in str(e):
                self._cleanup()
                raise RuntimeError("Browser window was closed by the user.")
            
        return page

    # ── Navigation ────────────────────────────────────────────────────────

    def navigate(self, url: str, tab_name: str = None, wait_until: str = "domcontentloaded") -> str:
        """Navigate to a URL."""
        if tab_name and tab_name in self._pages:
            # Use existing requested tab
            page = self._pages[tab_name]
            self._active_tab = tab_name
        else:
            # Always create a new tab (Ctrl+T) for new navigation to prevent overwriting
            from urllib.parse import urlparse
            if not tab_name:
                domain = urlparse(url).netloc.replace('www.', '') or "new_tab"
                tab_name = domain.split('.')[0]
            
            # Ensure tab name is unique
            base_name = tab_name
            counter = 1
            while tab_name in self._pages:
                tab_name = f"{base_name}_{counter}"
                counter += 1
                
            page = self._context.new_page()
            self._pages[tab_name] = page
            self._active_tab = tab_name

        try:
            response = page.goto(url, wait_until=wait_until, timeout=30000)
            status = response.status if response else "unknown"
            title = page.title()
            return f"Navigated to: {url}\nTitle: {title}\nStatus: {status}"
        except Exception as e:
            return f"Navigation error: {e}"

    def go_back(self, tab_name: str = None) -> str:
        """Go back in browser history."""
        page = self._get_page(tab_name)
        try:
            page.go_back(timeout=15000)
            return f"Went back. Now at: {page.url} — {page.title()}"
        except Exception as e:
            return f"Error going back: {e}"

    def go_forward(self, tab_name: str = None) -> str:
        """Go forward in browser history."""
        page = self._get_page(tab_name)
        try:
            page.go_forward(timeout=15000)
            return f"Went forward. Now at: {page.url} — {page.title()}"
        except Exception as e:
            return f"Error going forward: {e}"

    def reload(self, tab_name: str = None) -> str:
        """Reload the page."""
        page = self._get_page(tab_name)
        try:
            page.reload(timeout=15000)
            return f"Reloaded: {page.url}"
        except Exception as e:
            return f"Error reloading: {e}"

    # ── Interaction ───────────────────────────────────────────────────────

    def click(self, selector: str, tab_name: str = None) -> str:
        """Click an element by CSS selector or text."""
        page = self._get_page(tab_name)
        try:
            # Try CSS selector first
            try:
                page.click(selector, timeout=5000)
                return f"Clicked: {selector}"
            except Exception:
                pass

            # Try text-based click
            page.get_by_text(selector, exact=False).first.click(timeout=5000)
            return f"Clicked element with text: {selector}"
        except Exception as e:
            return f"Click failed for '{selector}': {e}"

    def type_text(self, selector: str, text: str, tab_name: str = None,
                  clear_first: bool = True) -> str:
        """Type text into an input field."""
        page = self._get_page(tab_name)
        try:
            # Try CSS selector
            try:
                if clear_first:
                    page.fill(selector, text, timeout=5000)
                else:
                    page.type(selector, text, timeout=5000)
                return f"Typed into '{selector}': {text[:50]}..."
            except Exception:
                pass

            # Try placeholder text
            try:
                element = page.get_by_placeholder(selector, exact=False).first
                if clear_first:
                    element.fill(text, timeout=5000)
                else:
                    element.type(text, timeout=5000)
                return f"Typed into field with placeholder '{selector}': {text[:50]}..."
            except Exception:
                pass

            # Try label
            element = page.get_by_label(selector, exact=False).first
            if clear_first:
                element.fill(text, timeout=5000)
            else:
                element.type(text, timeout=5000)
            return f"Typed into field labeled '{selector}': {text[:50]}..."

        except Exception as e:
            return f"Type failed for '{selector}': {e}"

    def press_key(self, key: str, tab_name: str = None) -> str:
        """Press a keyboard key (Enter, Tab, Escape, etc.)."""
        page = self._get_page(tab_name)
        try:
            # Sanitize common mistakes (Playwright expects "Control", not "ctrl")
            key = key.replace("ctrl+", "Control+").replace("alt+", "Alt+").replace("shift+", "Shift+")
            key = key.replace("Ctrl+", "Control+").replace("Alt+", "Alt+").replace("Shift+", "Shift+")
            
            page.keyboard.press(key)
            return f"Pressed key: {key}"
        except Exception as e:
            return f"Key press failed: {e}"

    def select_option(self, selector: str, value: str, tab_name: str = None) -> str:
        """Select an option from a dropdown."""
        page = self._get_page(tab_name)
        try:
            page.select_option(selector, value, timeout=5000)
            return f"Selected '{value}' in dropdown '{selector}'"
        except Exception as e:
            return f"Select failed: {e}"

    def scroll(self, direction: str = "down", amount: int = 500,
               tab_name: str = None) -> str:
        """Scroll the page."""
        page = self._get_page(tab_name)
        try:
            if direction == "down":
                page.mouse.wheel(0, amount)
            elif direction == "up":
                page.mouse.wheel(0, -amount)
            elif direction == "bottom":
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            elif direction == "top":
                page.evaluate("window.scrollTo(0, 0)")
            else:
                page.mouse.wheel(0, amount)

            return f"Scrolled {direction} by {amount}px"
        except Exception as e:
            return f"Scroll failed: {e}"

    # ── Content Extraction ────────────────────────────────────────────────

    def get_text(self, selector: str = "body", tab_name: str = None,
                 max_length: int = 5000) -> str:
        """Extract text content from the page or a specific element."""
        page = self._get_page(tab_name)
        try:
            if selector == "body":
                text = page.inner_text("body", timeout=5000)
            else:
                text = page.inner_text(selector, timeout=5000)

            # Clean up excessive whitespace
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            clean_text = "\n".join(lines)

            if len(clean_text) > max_length:
                clean_text = clean_text[:max_length] + f"\n\n[... truncated, {len(clean_text)} total chars]"

            url = page.url
            title = page.title()
            return f"URL: {url}\nTitle: {title}\n\n{clean_text}"
        except Exception as e:
            return f"Error extracting text: {e}"

    def get_html(self, selector: str = "body", tab_name: str = None) -> str:
        """Get HTML content of an element."""
        page = self._get_page(tab_name)
        try:
            html = page.inner_html(selector, timeout=5000)
            if len(html) > 5000:
                html = html[:5000] + "\n[... truncated]"
            return html
        except Exception as e:
            return f"Error getting HTML: {e}"

    def get_links(self, tab_name: str = None, max_links: int = 30) -> str:
        """Extract all links from the current page."""
        page = self._get_page(tab_name)
        try:
            links = page.evaluate("""
                () => {
                    const anchors = document.querySelectorAll('a[href]');
                    return Array.from(anchors).slice(0, %d).map(a => ({
                        text: a.innerText.trim().substring(0, 80),
                        href: a.href
                    })).filter(l => l.text && l.href);
            """ % max_links)

            if not links:
                return "No links found on this page."

            lines = [f"Links on {page.url}:", ""]
            for i, link in enumerate(links, 1):
                lines.append(f"  {i}. [{link['text']}]({link['href']})")

            return "\n".join(lines)
        except Exception as e:
            return f"Error extracting links: {e}"

    def get_elements(self, tab_name: str = None) -> str:
        """Get all interactive elements (buttons, inputs, links) from the page."""
        page = self._get_page(tab_name)
        try:
            elements = page.evaluate("""
                () => {
                    const interactables = document.querySelectorAll('button, input, select, textarea, [role="button"], [role="link"], a');
                    const results = [];
                    let count = 0;
                    for (const el of interactables) {
                        if (count >= 50) break; // Limit to prevent massive payloads
                        
                        // Check if visible
                        const style = window.getComputedStyle(el);
                        if (style.display === 'none' || style.visibility === 'hidden' || el.offsetWidth === 0) continue;
                        
                        let text = (el.innerText || el.value || el.placeholder || el.getAttribute('aria-label') || '').trim().substring(0, 50);
                        if (!text && el.tagName.toLowerCase() !== 'input') continue;
                        
                        const tag = el.tagName.toLowerCase();
                        let selector = tag;
                        if (el.id) selector += `#${el.id}`;
                        else if (el.className && typeof el.className === 'string') {
                            selector += `.${el.className.trim().split(/\s+/).join('.')}`;
                        }
                        
                        // Limit selector length
                        if (selector.length > 50) selector = tag;
                        
                        const role = el.getAttribute('role');
                        const type = el.getAttribute('type');
                        
                        results.push(`[${tag}${type ? ' type='+type : ''}${role ? ' role='+role : ''}] Text: "${text}" | Selector: "${selector}"`);
                        count++;
                    }
                    return results;
                }
            """)
            if not elements:
                return "No interactive elements found on page."
            return "Interactive Elements (Visible):\n" + "\n".join(elements)
        except Exception as e:
            return f"Error extracting elements: {e}"

    def get_page_info(self, tab_name: str = None) -> str:
        """Get current page info (URL, title, etc.)."""
        page = self._get_page(tab_name)
        try:
            return (
                f"URL: {page.url}\n"
                f"Title: {page.title()}\n"
                f"Tab: {tab_name or self._active_tab}"
            )
        except Exception as e:
            return f"Error getting page info: {e}"

    # ── Screenshots ───────────────────────────────────────────────────────

    def screenshot(self, path: str = None, full_page: bool = False,
                   tab_name: str = None) -> str:
        """Take a screenshot of the current page."""
        page = self._get_page(tab_name)
        try:
            if not path:
                screenshots_dir = RAGE_DIR / "screenshots"
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                timestamp = int(time.time())
                path = str(screenshots_dir / f"screenshot_{timestamp}.png")

            page.screenshot(path=path, full_page=full_page)
            return f"Screenshot saved: {path}"
        except Exception as e:
            return f"Screenshot failed: {e}"

    # ── Tab Management ────────────────────────────────────────────────────

    def new_tab(self, name: str, url: str = None) -> str:
        """Create a new browser tab."""
        if name in self._pages:
            return f"Tab '{name}' already exists. Use a different name."

        try:
            page = self._context.new_page()
            self._pages[name] = page
            self._active_tab = name

            if url:
                response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                return f"New tab '{name}' opened at {url} (status: {response.status if response else 'ok'})"

            return f"New tab '{name}' created (blank page)."
        except Exception as e:
            return f"Error creating tab: {e}"

    def switch_tab(self, name: str) -> str:
        """Switch to a different tab."""
        if name not in self._pages:
            tabs = ", ".join(self._pages.keys())
            return f"Tab '{name}' not found. Available: {tabs}"

        self._active_tab = name
        page = self._pages[name]
        try:
            page.bring_to_front()
            return f"Switched to tab '{name}' — {page.url}"
        except Exception as e:
            return f"Switched to tab '{name}' (error bringing to front: {e})"

    def close_tab(self, name: str) -> str:
        """Close a browser tab."""
        if name not in self._pages:
            return f"Tab '{name}' not found."
        if name == self._active_tab and len(self._pages) == 1:
            return "Cannot close the last tab. Use browser_close to close the browser."

        try:
            self._pages[name].close()
            del self._pages[name]

            if name == self._active_tab:
                self._active_tab = next(iter(self._pages))

            return f"Tab '{name}' closed. Active tab: {self._active_tab}"
        except Exception as e:
            return f"Error closing tab: {e}"

    def list_tabs(self) -> str:
        """List all open tabs."""
        if not self._pages:
            return "No tabs open."

        lines = ["Browser Tabs:", ""]
        for name, page in self._pages.items():
            active = " ◄ (active)" if name == self._active_tab else ""
            try:
                url = page.url
                title = page.title()
            except Exception:
                url = "(unknown)"
                title = "(unknown)"
            lines.append(f"  🌐 {name}{active}  —  {title[:40]}  ({url[:60]})")

        return "\n".join(lines)

    # ── Web Search (DuckDuckGo) ─────────────────────────────────────────────────────

    def google_search(self, query: str, tab_name: str = None) -> str:
        """Perform a DuckDuckGo search (bypassing Google CAPTCHAs) and return results."""
        page = self._get_page(tab_name)
        try:
            import urllib.parse
            url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}"
            page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for results
            page.wait_for_timeout(2000)

            # Extract search results
            results = page.evaluate("""
                () => {
                    const items = document.querySelectorAll('article[data-testid="result"]');
                    return Array.from(items).slice(0, 10).map(item => {
                        const titleEl = item.querySelector('a[data-testid="result-title-a"]');
                        const snippetEl = item.querySelector('div[data-result="snippet"]');
                        return {
                            title: titleEl ? titleEl.innerText : '',
                            url: titleEl ? titleEl.href : '',
                            snippet: snippetEl ? snippetEl.innerText.substring(0, 200) : ''
                        };
                    }).filter(r => r.title && r.url);
                }
            """)

            if not results:
                # Fallback: get all text
                text = page.inner_text("body")
                return f"Search results for '{query}':\n\n{text[:3000]}"

            lines = [f"Search: '{query}'", ""]
            for i, r in enumerate(results, 1):
                lines.append(f"  {i}. **{r['title']}**")
                lines.append(f"     {r['url']}")
                if r.get("snippet"):
                    lines.append(f"     {r['snippet']}")
                lines.append("")

            return "\n".join(lines)
        except Exception as e:
            return f"Search error: {e}"

    # ── File Upload / Download ────────────────────────────────────────────

    def upload_file(self, selector: str, file_path: str,
                    tab_name: str = None) -> str:
        """Upload a file to a file input."""
        page = self._get_page(tab_name)
        try:
            file_path = os.path.expanduser(file_path)
            if not os.path.exists(file_path):
                return f"File not found: {file_path}"

            page.set_input_files(selector, file_path, timeout=5000)
            return f"Uploaded: {file_path}"
        except Exception as e:
            return f"Upload failed: {e}"

    def wait_for_download(self, tab_name: str = None) -> str:
        """Wait for and return info about the next download."""
        page = self._get_page(tab_name)
        try:
            with page.expect_download(timeout=30000) as download_info:
                pass
            download = download_info.value
            save_path = os.path.join(self._downloads_dir, download.suggested_filename)
            download.save_as(save_path)
            return f"Downloaded: {save_path}"
        except Exception as e:
            return f"Download error: {e}"

    # ── JavaScript Evaluation ─────────────────────────────────────────────

    def evaluate_js(self, script: str, tab_name: str = None) -> str:
        """Evaluate JavaScript on the page."""
        page = self._get_page(tab_name)
        try:
            result = page.evaluate(script)
            return f"JS Result: {json.dumps(result, default=str)[:3000]}"
        except Exception as e:
            return f"JS evaluation error: {e}"

    # ── Wait ──────────────────────────────────────────────────────────────

    def wait_for(self, selector: str, state: str = "visible",
                 timeout: int = 10000, tab_name: str = None) -> str:
        """Wait for an element to appear."""
        page = self._get_page(tab_name)
        try:
            page.wait_for_selector(selector, state=state, timeout=timeout)
            return f"Element found: {selector}"
        except Exception as e:
            return f"Wait timeout for '{selector}': {e}"


# ── Tool Classes ──────────────────────────────────────────────────────────────

class BrowserOpenTool(BaseTool):
    """Navigate to a URL in the browser."""

    name = "browser_open"
    description = (
        "Open a URL in the browser. Launches the browser with a persistent profile if not already running. "
        "Cookies, sessions, and logins are retained across sessions so the user only needs to log in once. "
        "Use for browsing websites, accessing dashboards, Google services, etc."
    )
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to navigate to",
            },
            "tab_name": {
                "type": "string",
                "description": "Tab name to use (default: active tab)",
            },
            "headless": {
                "type": "boolean",
                "description": "Run browser without visible window (default: true). Set false to show the browser.",
            },
        },
        "required": ["url"],
    }

    def execute(self, url: str, tab_name: str = None,
                headless: bool = False) -> ToolResult:
        session = BrowserSession.get_instance()

        # Auto-launch if not running
        if not session.is_running:
            launch_msg = session.launch(headless=headless)
            if "Error" in launch_msg:
                return ToolResult(success=False, output="", error=launch_msg)

        result = session.navigate(url, tab_name=tab_name)
        success = "error" not in result.lower()
        return ToolResult(success=success, output=result, error="" if success else result)


class BrowserClickTool(BaseTool):
    """Click an element on the page."""

    name = "browser_click"
    description = (
        "Click an element on the current page. You can use a CSS selector (e.g., '#submit-btn', '.nav-link') "
        "or the visible text of the element (e.g., 'Sign In', 'Next', 'Submit')."
    )
    parameters = {
        "type": "object",
        "properties": {
            "selector": {
                "type": "string",
                "description": "CSS selector or visible text of the element to click",
            },
            "tab_name": {
                "type": "string",
                "description": "Tab to click in (default: active tab)",
            },
        },
        "required": ["selector"],
    }

    def execute(self, selector: str, tab_name: str = None) -> ToolResult:
        session = BrowserSession.get_instance()
        if not session.is_running:
            return ToolResult(success=False, output="", error="Browser is not running. Use browser_open first.")

        result = session.click(selector, tab_name=tab_name)
        success = "failed" not in result.lower() and "error" not in result.lower()
        return ToolResult(success=success, output=result, error="" if success else result)


class BrowserTypeTool(BaseTool):
    """Type text into a form field."""

    name = "browser_type"
    description = (
        "Type text into an input field on the page. Use CSS selector, placeholder text, "
        "or label to identify the field. Set clear_first=false to append instead of replacing."
    )
    parameters = {
        "type": "object",
        "properties": {
            "selector": {
                "type": "string",
                "description": "CSS selector, placeholder text, or label of the input field",
            },
            "text": {
                "type": "string",
                "description": "Text to type into the field",
            },
            "clear_first": {
                "type": "boolean",
                "description": "Clear the field before typing (default: true)",
            },
            "tab_name": {
                "type": "string",
                "description": "Tab to type in (default: active tab)",
            },
        },
        "required": ["selector", "text"],
    }

    def execute(self, selector: str, text: str, clear_first: bool = True,
                tab_name: str = None) -> ToolResult:
        session = BrowserSession.get_instance()
        if not session.is_running:
            return ToolResult(success=False, output="", error="Browser is not running. Use browser_open first.")

        result = session.type_text(selector, text, tab_name=tab_name, clear_first=clear_first)
        success = "failed" not in result.lower() and "error" not in result.lower()
        return ToolResult(success=success, output=result, error="" if success else result)


class BrowserReadTool(BaseTool):
    """Read/extract text content from the page."""

    name = "browser_read"
    description = (
        "Extract text content from the current page. By default reads the full page body. "
        "You can specify a CSS selector to read a specific section. "
        "Use this to read articles, extract data, check page content, summarize webpages."
    )
    parameters = {
        "type": "object",
        "properties": {
            "selector": {
                "type": "string",
                "description": "CSS selector of element to read (default: 'body' = full page)",
            },
            "tab_name": {
                "type": "string",
                "description": "Tab to read from (default: active tab)",
            },
        },
        "required": [],
    }

    def execute(self, selector: str = "body", tab_name: str = None) -> ToolResult:
        session = BrowserSession.get_instance()
        if not session.is_running:
            return ToolResult(success=False, output="", error="Browser is not running. Use browser_open first.")

        result = session.get_text(selector, tab_name=tab_name)
        success = "error" not in result.lower()[:20]
        return ToolResult(success=success, output=result, error="" if success else result)


class BrowserScreenshotTool(BaseTool):
    """Take a screenshot of the current page."""

    name = "browser_screenshot"
    description = (
        "Take a screenshot of the current page and save it as a PNG file. "
        "Useful for capturing visual state, debugging, or providing evidence."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path to save screenshot (default: auto-generated in ~/.rage/screenshots/)",
            },
            "full_page": {
                "type": "boolean",
                "description": "Capture full page including scrollable content (default: false)",
            },
            "tab_name": {
                "type": "string",
                "description": "Tab to screenshot (default: active tab)",
            },
        },
        "required": [],
    }

    def execute(self, path: str = None, full_page: bool = False,
                tab_name: str = None) -> ToolResult:
        session = BrowserSession.get_instance()
        if not session.is_running:
            return ToolResult(success=False, output="", error="Browser is not running. Use browser_open first.")

        result = session.screenshot(path=path, full_page=full_page, tab_name=tab_name)
        success = "saved" in result.lower()
        return ToolResult(success=success, output=result, error="" if success else result)


class BrowserVisionTool(BaseTool):
    """Take a screenshot and analyze it with a vision model."""

    name = "browser_vision"
    description = (
        "Take a screenshot of the current page and ask a visual question about it. "
        "Useful for understanding layout, finding un-selectable elements, or reading visual state."
    )
    parameters = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Question to ask about the visual state of the page",
            },
            "tab_name": {
                "type": "string",
                "description": "Tab to analyze (default: active tab)",
            },
        },
        "required": ["question"],
    }

    def execute(self, question: str, tab_name: str = None) -> ToolResult:
        session = BrowserSession.get_instance()
        if not session.is_running:
            return ToolResult(success=False, output="", error="Browser is not running. Use browser_open first.")

        try:
            import base64
            import tempfile
            import requests
            import json
            from rage.config import load_config, get_api_key, get_github_token, get_groq_api_key, get_nvidia_api_key
            
            # Take a temporary screenshot
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                ss_path = tmp.name
                
            session.screenshot(path=ss_path, full_page=False, tab_name=tab_name)
            
            # Read and encode
            with open(ss_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                
            # Make API call directly with current model for vision
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
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1024
            }


            
            response = requests.post(
                api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            vision_result = data["choices"][0]["message"]["content"]
            
            # Cleanup temp file
            import os
            try:
                os.unlink(ss_path)
            except Exception:
                pass
                
            return ToolResult(success=True, output=f"Vision Analysis for '{question}':\n\n{vision_result}")
            
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Vision analysis failed: {e}")



class BrowserScrollTool(BaseTool):
    """Scroll the page."""

    name = "browser_scroll"
    description = (
        "Scroll the page up, down, to top, or to bottom. "
        "Use direction='down' or 'up' with an amount in pixels, "
        "or 'top'/'bottom' to jump to the start/end."
    )
    parameters = {
        "type": "object",
        "properties": {
            "direction": {
                "type": "string",
                "description": "Scroll direction: 'down', 'up', 'top', 'bottom' (default: 'down')",
            },
            "amount": {
                "type": "integer",
                "description": "Pixels to scroll (default: 500). Ignored for 'top'/'bottom'.",
            },
            "tab_name": {
                "type": "string",
                "description": "Tab to scroll (default: active tab)",
            },
        },
        "required": [],
    }

    def execute(self, direction: str = "down", amount: int = 500,
                tab_name: str = None) -> ToolResult:
        session = BrowserSession.get_instance()
        if not session.is_running:
            return ToolResult(success=False, output="", error="Browser is not running. Use browser_open first.")

        result = session.scroll(direction, amount, tab_name=tab_name)
        return ToolResult(success=True, output=result)


class BrowserSearchTool(BaseTool):
    """Search Google."""

    name = "browser_search"
    description = (
        "Perform a Google search and return the top results with titles, URLs, and snippets. "
        "Use this for web research, finding information, looking up documentation."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query",
            },
            "tab_name": {
                "type": "string",
                "description": "Tab to search in (default: active tab)",
            },
        },
        "required": ["query"],
    }

    def execute(self, query: str, tab_name: str = None) -> ToolResult:
        session = BrowserSession.get_instance()

        # Auto-launch if not running (force headless=False so user sees it)
        if not session.is_running:
            launch_msg = session.launch(headless=False)
            if "Error" in launch_msg:
                return ToolResult(success=False, output="", error=launch_msg)

        result = session.google_search(query, tab_name=tab_name)
        success = "error" not in result.lower()[:20]
        return ToolResult(success=success, output=result, error="" if success else result)


class BrowserTabsTool(BaseTool):
    """Manage browser tabs."""

    name = "browser_tabs"
    description = (
        "Manage browser tabs. Actions: 'list' (show all tabs), 'new' (create tab), "
        "'switch' (switch to tab), 'close' (close tab)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Tab action: 'list', 'new', 'switch', 'close'",
            },
            "name": {
                "type": "string",
                "description": "Tab name (required for new/switch/close)",
            },
            "url": {
                "type": "string",
                "description": "URL to open in new tab (optional, only for 'new' action)",
            },
        },
        "required": ["action"],
    }

    def execute(self, action: str, name: str = None,
                url: str = None) -> ToolResult:
        session = BrowserSession.get_instance()
        if not session.is_running and action != "list":
            return ToolResult(success=False, output="", error="Browser is not running. Use browser_open first.")

        if action == "list":
            if not session.is_running:
                return ToolResult(success=True, output="Browser is not running. No tabs.")
            result = session.list_tabs()
        elif action == "new":
            if not name:
                name = f"tab_{len(session._pages) + 1}"
            result = session.new_tab(name, url=url)
        elif action == "switch":
            if not name:
                return ToolResult(success=False, output="", error="Tab name is required for 'switch' action.")
            result = session.switch_tab(name)
        elif action == "close":
            if not name:
                return ToolResult(success=False, output="", error="Tab name is required for 'close' action.")
            result = session.close_tab(name)
        else:
            return ToolResult(success=False, output="", error=f"Unknown tab action: {action}. Use list/new/switch/close.")

        success = "error" not in result.lower()
        return ToolResult(success=success, output=result, error="" if success else result)


class BrowserKeyTool(BaseTool):
    """Press keyboard keys in the browser."""

    name = "browser_key"
    description = (
        "Press a keyboard key or key combination. "
        "Use for submitting forms (Enter), navigation (Tab), closing dialogs (Escape), etc."
    )
    parameters = {
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "Key to press: 'Enter', 'Tab', 'Escape', 'Backspace', 'ArrowDown', 'Control+a', etc.",
            },
            "tab_name": {
                "type": "string",
                "description": "Tab to press key in (default: active tab)",
            },
        },
        "required": ["key"],
    }

    def execute(self, key: str, tab_name: str = None) -> ToolResult:
        session = BrowserSession.get_instance()
        if not session.is_running:
            return ToolResult(success=False, output="", error="Browser is not running. Use browser_open first.")

        result = session.press_key(key, tab_name=tab_name)
        success = "failed" not in result.lower()
        return ToolResult(success=success, output=result, error="" if success else result)


class BrowserCloseTool(BaseTool):
    """Close the browser."""

    name = "browser_close"
    description = (
        "Close the browser and save the persistent profile. "
        "All cookies, sessions, and logins will be preserved for the next session."
    )
    parameters = {
        "type": "object",
        "properties": {},
    }

    def execute(self) -> ToolResult:
        session = BrowserSession.get_instance()
        result = session.close()
        success = "error" not in result.lower()
        return ToolResult(success=success, output=result, error="" if success else result)


class BrowserLinksTool(BaseTool):
    """Extract links from the current page."""

    name = "browser_links"
    description = (
        "Extract all links from the current page with their text and URLs. "
        "Useful for finding navigation options, locating specific pages, or scraping link data."
    )
    parameters = {
        "type": "object",
        "properties": {
            "tab_name": {
                "type": "string",
                "description": "Tab to extract links from (default: active tab)",
            },
        },
        "required": [],
    }

    def execute(self, tab_name: str = None) -> ToolResult:
        session = BrowserSession.get_instance()
        if not session.is_running:
            return ToolResult(success=False, output="", error="Browser is not running. Use browser_open first.")

        result = session.get_links(tab_name=tab_name)
        return ToolResult(success=True, output=result)


class BrowserElementsTool(BaseTool):
    """Extract interactive elements from the current page."""

    name = "browser_elements"
    description = (
        "Extract visible interactive elements (buttons, inputs, selects) from the current page. "
        "Returns their text content and suggested CSS selectors to use with browser_click or browser_type."
    )
    parameters = {
        "type": "object",
        "properties": {
            "tab_name": {
                "type": "string",
                "description": "Tab to extract elements from (default: active tab)",
            },
        },
        "required": [],
    }

    def execute(self, tab_name: str = None) -> ToolResult:
        session = BrowserSession.get_instance()
        if not session.is_running:
            return ToolResult(success=False, output="", error="Browser is not running. Use browser_open first.")

        result = session.get_elements(tab_name=tab_name)
        return ToolResult(success=True, output=result)


class BrowserJSTool(BaseTool):
    """Evaluate JavaScript on the page."""

    name = "browser_js"
    description = (
        "Execute JavaScript code on the current page and return the result. "
        "Use for advanced DOM manipulation, data extraction, or interacting with web apps."
    )
    parameters = {
        "type": "object",
        "properties": {
            "script": {
                "type": "string",
                "description": "JavaScript code to evaluate",
            },
            "tab_name": {
                "type": "string",
                "description": "Tab to execute in (default: active tab)",
            },
        },
        "required": ["script"],
    }

    def execute(self, script: str, tab_name: str = None) -> ToolResult:
        session = BrowserSession.get_instance()
        if not session.is_running:
            return ToolResult(success=False, output="", error="Browser is not running. Use browser_open first.")

        result = session.evaluate_js(script, tab_name=tab_name)
        success = "error" not in result.lower()[:20]
        return ToolResult(success=success, output=result, error="" if success else result)


class BrowserWaitTool(BaseTool):
    """Wait for an element to appear on the page."""

    name = "browser_wait"
    description = (
        "Wait for an element matching a CSS selector to appear on the page. "
        "Useful before clicking or interacting with dynamically loaded content."
    )
    parameters = {
        "type": "object",
        "properties": {
            "selector": {
                "type": "string",
                "description": "CSS selector to wait for",
            },
            "state": {
                "type": "string",
                "description": "State to wait for: 'visible', 'hidden', 'attached', 'detached' (default: 'visible')",
            },
            "timeout": {
                "type": "integer",
                "description": "Max wait time in milliseconds (default: 10000)",
            },
            "tab_name": {
                "type": "string",
                "description": "Tab to wait in (default: active tab)",
            },
        },
        "required": ["selector"],
    }

    def execute(self, selector: str, state: str = "visible",
                timeout: int = 10000, tab_name: str = None) -> ToolResult:
        session = BrowserSession.get_instance()
        if not session.is_running:
            return ToolResult(success=False, output="", error="Browser is not running. Use browser_open first.")

        result = session.wait_for(selector, state=state, timeout=timeout, tab_name=tab_name)
        success = "found" in result.lower()
        return ToolResult(success=success, output=result, error="" if success else result)