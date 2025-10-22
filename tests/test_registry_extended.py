import sys
import importlib
from pathlib import Path
import shutil


def test_registry_discovers_subpackages(tmp_path):
    # Prepare a temporary subpackage under src/agents
    project_root = Path(__file__).parent.parent
    agents_dir = project_root / "src" / "agents"
    pkg_dir = agents_dir / "tmp_pkg"
    (pkg_dir / "__init__.py").parent.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
    (pkg_dir / "temp_agent.py").write_text(
        """
from agents.base import Agent, AgentConfig
from typing import Any

class TempAgent(Agent):
    def run(self, **kwargs: Any) -> Any:
        return "temp"
""".lstrip(),
        encoding="utf-8",
    )

    try:
        # Reload agents package to pick new module
        import agents as agents_module

        importlib.reload(agents_module)
        assert "TempAgent" in agents_module.AGENT_REGISTRY
    finally:
        # Cleanup and reload to restore clean state
        shutil.rmtree(pkg_dir, ignore_errors=True)
        import agents as agents_module
        importlib.reload(agents_module)


def test_import_errors_are_reported():
    # Create a broken module in agents dir
    project_root = Path(__file__).parent.parent
    agents_dir = project_root / "src" / "agents"
    broken_file = agents_dir / "tmp_broken_test.py"
    broken_file.write_text("raise ImportError('broken for test')\n", encoding="utf-8")
    try:
        import agents as agents_module

        importlib.reload(agents_module)
        # Fully-qualified module name in errors
        broken_modname = "agents.tmp_broken_test"
        assert broken_modname in agents_module.AGENT_IMPORT_ERRORS
        assert "ImportError" in agents_module.AGENT_IMPORT_ERRORS[broken_modname]
    finally:
        try:
            broken_file.unlink()
        except FileNotFoundError:
            pass
        import agents as agents_module
        importlib.reload(agents_module)
