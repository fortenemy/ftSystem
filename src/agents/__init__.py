
import pkgutil
import importlib
import inspect
from pathlib import Path

from .base import Agent

AGENT_REGISTRY = {}

# Get the current package path (src/agents)
package_path = Path(__file__).parent
package_name = __name__

for module_info in pkgutil.iter_modules([str(package_path)]):
    module_name = module_info.name
    # Skip base.py and private modules
    if module_name.startswith("_") or module_name == "base":
        continue

    # Import the module (e.g., src.agents.hello_agent)
    full_module_name = f"{package_name}.{module_name}"
    module = importlib.import_module(full_module_name)

    # Inspect all classes in the module
    for name, obj in inspect.getmembers(module, inspect.isclass):
        # Only include classes that are subclass of Agent, but not Agent itself
        if issubclass(obj, Agent) and obj is not Agent:
            AGENT_REGISTRY[name] = obj

# Optionally: expose AGENT_REGISTRY for import
__all__ = ["AGENT_REGISTRY"]