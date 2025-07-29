
import sys
from pathlib import Path

# Ensure src/ is in sys.path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest
from agents import AGENT_REGISTRY
from agents.base import AgentConfig

def test_agent_registry_listing():
    """Test that at least one agent is registered."""
    assert len(AGENT_REGISTRY) > 0
    assert "HelloAgent" in AGENT_REGISTRY

def test_hello_agent_run(capsys):
    """Test that HelloAgent.run() prints the expected output."""
    agent_cls = AGENT_REGISTRY["HelloAgent"]
    config = AgentConfig(name="hello", description="pytest config")
    agent = agent_cls(config)
    agent.run()
    captured = capsys.readouterr()
    assert "Hello, world!" in captured.out