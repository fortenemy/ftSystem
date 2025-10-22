import importlib
from importlib import metadata as im


def test_entry_points_registers_external_agent(monkeypatch):
    class FakeEP:
        def load(self):
            from agents.base import Agent, AgentConfig

            class EPAgent(Agent):
                def __init__(self, config: AgentConfig):
                    super().__init__(config)

                def run(self, **kwargs):
                    return "ep"

            return EPAgent

    class FakeEPS:
        def select(self, group=None):
            return [FakeEP()] if group == "ftsystem.agents" else []

    monkeypatch.setattr(im, "entry_points", lambda: FakeEPS())
    import agents as agents_module

    importlib.reload(agents_module)
    assert "EPAgent" in agents_module.AGENT_REGISTRY

