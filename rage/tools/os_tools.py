import os
import sys
import time
import subprocess
import pyautogui
from rage.tools.base import BaseTool, ToolResult

class OpenAppTool(BaseTool):
    """Launch an application natively in the OS."""
    name = "os_open_app"
    description = "Launch an application natively in the OS (e.g., 'firefox', 'code', 'spotify', 'gnome-terminal')."
    parameters = {
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "Name of the application or executable to launch.",
            }
        },
        "required": ["app_name"],
    }
    
    def execute(self, app_name: str) -> ToolResult:
        app = app_name.strip()
        if not app:
            return ToolResult(success=False, output="", error="Missing app name")
        try:
            if sys.platform == "win32":
                subprocess.Popen(f"start {app}", shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-a", app])
            else:
                subprocess.Popen([app])
            # Sleep briefly to give it time to open
            time.sleep(2)
            return ToolResult(success=True, output=f"Launched application: {app}")
        except Exception as e:
            # Fallback to shell invocation if list fails
            try:
                subprocess.Popen(app, shell=True)
                time.sleep(2)
                return ToolResult(success=True, output=f"Launched application via shell fallback: {app}")
            except Exception as e2:
                return ToolResult(success=False, output="", error=f"Failed to launch app: {e} | {e2}")

class KeyboardPressTool(BaseTool):
    """Press a single key or key combination globally."""
    name = "os_keyboard_press"
    description = "Press a single key or key combination globally (e.g., 'enter', 'ctrl+c', 'win+d', 'alt+tab')."
    parameters = {
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "Key or combination to press. Use '+' for combinations.",
            }
        },
        "required": ["key"],
    }
    
    _MODIFIERS = {"alt", "ctrl", "shift", "win", "winleft", "winright", "command"}
    _KEY_ALIASES = {
        "windows": "win", "cmd": "win", "control": "ctrl",
        "return": "enter", "esc": "escape", "del": "delete",
        "pageup": "pageup", "pagedown": "pagedown",
        "arrowup": "up", "arrowdown": "down",
        "arrowleft": "left", "arrowright": "right",
    }
    
    def _normalize(self, k: str):
        k = k.strip().lower()
        return self._KEY_ALIASES.get(k, k)
        
    def execute(self, key: str) -> ToolResult:
        try:
            parts = [self._normalize(k) for k in key.split("+")]
            
            if len(parts) == 1:
                k = parts[0]
                if k.endswith("_down"):
                    pyautogui.keyDown(k[:-5])
                    return ToolResult(success=True, output=f"Held down key: {k[:-5]}")
                elif k.endswith("_up"):
                    pyautogui.keyUp(k[:-3])
                    return ToolResult(success=True, output=f"Released key: {k[:-3]}")
                else:
                    pyautogui.press(k)
                    return ToolResult(success=True, output=f"Pressed key: {key}")
                    
            modifiers = []
            regulars = []
            for p in parts:
                if p in self._MODIFIERS and p not in modifiers:
                    modifiers.append(p)
                elif p not in self._MODIFIERS:
                    regulars.append(p)
                    
            if not regulars:
                pyautogui.hotkey(*parts)
                return ToolResult(success=True, output=f"Pressed hotkey: {key}")
                
            for m in modifiers:
                pyautogui.keyDown(m)
                time.sleep(0.05)
                
            for r in regulars:
                pyautogui.press(r)
                time.sleep(0.1)
                
            time.sleep(0.1)
            
            for m in reversed(modifiers):
                pyautogui.keyUp(m)
                time.sleep(0.05)
                
            return ToolResult(success=True, output=f"Pressed key combo: {key}")
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Keyboard press failed: {e}")

class KeyboardTypeTool(BaseTool):
    """Type text globally as if typed on a physical keyboard."""
    name = "os_keyboard_type"
    description = "Type text globally as if typed on a physical keyboard. Ensure the correct application is focused first."
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to type.",
            },
            "interval": {
                "type": "number",
                "description": "Seconds between key presses (default: 0.01).",
            }
        },
        "required": ["text"],
    }
    def execute(self, text: str, interval: float = 0.01) -> ToolResult:
        try:
            pyautogui.write(text, interval=interval)
            return ToolResult(success=True, output=f"Successfully typed {len(text)} characters.")
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Keyboard type failed: {e}")
