import os
import sys
import importlib.util
import inspect
from pathlib import Path
from rage.tools.base import BaseTool

def load_plugins(registry) -> list[str]:
    """
    Scans ~/.rage/plugins/ for .py files, loads them, 
    and registers any BaseTool classes with the provided registry.
    Returns a list of loaded plugin tool names.
    """
    plugins_dir = Path.home() / ".rage" / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    
    loaded_tools = []
    
    # Add plugins dir to sys.path so plugins can import each other if needed
    if str(plugins_dir) not in sys.path:
        sys.path.insert(0, str(plugins_dir))
        
    for file_path in plugins_dir.glob("*.py"):
        if file_path.name.startswith("_"):
            continue
            
        module_name = f"rage_plugin_{file_path.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                continue
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Find all classes that inherit from BaseTool (but aren't BaseTool itself)
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseTool) and obj is not BaseTool and obj.__module__ == module_name:
                    tool_instance = obj()
                    if hasattr(tool_instance, 'name'):
                        registry.register(tool_instance)
                        loaded_tools.append(tool_instance.name)
                        
        except Exception as e:
            # We silently ignore broken plugins but print to console for debugging if running interactively
            print(f"[Warning] Failed to load plugin {file_path.name}: {e}")
            
    return loaded_tools
