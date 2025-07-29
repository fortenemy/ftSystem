
from agents import AGENT_REGISTRY
from agents.base import AgentConfig

def test_agent_registry_listing():
    print("Discovered agents:", list(AGENT_REGISTRY.keys()))
    assert len(AGENT_REGISTRY) > 0, "No agents found in AGENT_REGISTRY!"

def test_hello_agent_run():
    if "HelloAgent" in AGENT_REGISTRY:
        agent_cls = AGENT_REGISTRY["HelloAgent"]
        config = AgentConfig(name="HelloAgent", description="Test agent")
        agent = agent_cls(config)
        result = agent.run()
        print("HelloAgent.run() result:", result)
        # Optionally, check the result if you know what to expect
        assert isinstance(result, str) or result is None
    else:
        print("HelloAgent not found in registry.")
        assert False, "HelloAgent not found in AGENT_REGISTRY!"

if __name__ == "__main__":
    test_agent_registry_listing()
    test_hello_agent_run()