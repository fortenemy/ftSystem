
import pkgutil
import importlib
import inspect
from pathlib import Path
from typing import Dict

from .base import Agent

AGENT_REGISTRY: Dict[str, type[Agent]] = {}
AGENT_IMPORT_ERRORS: Dict[str, str] = {}

# Get the current package path (src/agents)
package_path = Path(__file__).parent
package_name = __name__

# Walk through all subpackages and modules under src/agents
for finder, modname, ispkg in pkgutil.walk_packages([str(package_path)], prefix=f"{package_name}."):
    # Skip private modules and the base module
    if modname.endswith(".base") or any(part.startswith("_") for part in modname.split(".")):
        continue
    try:
        module = importlib.import_module(modname)
    except Exception as e:
        # Record import errors for diagnostics
        AGENT_IMPORT_ERRORS[modname] = f"{type(e).__name__}: {e}"
        continue

    # Inspect all classes in the module
    for name, obj in inspect.getmembers(module, inspect.isclass):
        # Only include classes that are subclass of Agent, but not Agent itself
        try:
            if issubclass(obj, Agent) and obj is not Agent:
                # Last one wins on name collision
                AGENT_REGISTRY[name] = obj
        except Exception:
            # Some objects may not be suitable for issubclass in edge cases
            continue

# Load external agent entry points, if any
try:
    try:
        from importlib.metadata import entry_points  # py3.10+
    except Exception:  # pragma: no cover
        entry_points = None  # type: ignore

    if entry_points is not None:  # pragma: no cover (covered via monkeypatch in tests)
        eps = entry_points()
        group_eps = getattr(eps, "select", None)
        if callable(group_eps):
            selected = eps.select(group="ftsystem.agents")
        else:
            selected = eps.get("ftsystem.agents", [])  # type: ignore[attr-defined]
        for ep in selected:
            try:
                obj = ep.load()
                if inspect.isclass(obj) and issubclass(obj, Agent) and obj is not Agent:
                    AGENT_REGISTRY[obj.__name__] = obj
            except Exception as e:
                AGENT_IMPORT_ERRORS[str(ep)] = f"{type(e).__name__}: {e}"
except Exception:
    # Ignore entry point loading failures silently here
    pass

# Expose registries for import
__all__ = ["AGENT_REGISTRY", "AGENT_IMPORT_ERRORS"]
