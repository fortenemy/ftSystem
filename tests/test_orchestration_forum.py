import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from agents import AGENT_REGISTRY
from agents.base import AgentConfig


def test_master_agent_forum_transcript():
    assert "MasterAgent" in AGENT_REGISTRY
    cls = AGENT_REGISTRY["MasterAgent"]
    agent = cls(AgentConfig(name="master", description="test"))
    res = agent.run(input="What time is it?")
    assert isinstance(res, dict)
    assert "results" in res
    assert "transcript" in res
    transcript = res["transcript"]
    # Expect at least a system start and a user message
    roles = [m.get("role") for m in transcript]
    assert "system" in roles
    assert "user" in roles
    # Expect HelloAgent contribution present in results and transcript
    assert "HelloAgent" in res.get("results", {})
    has_hello = any(m.get("agent") == "HelloAgent" for m in transcript if m.get("role") == "agent")
    assert has_hello

