# ftSystem Plugins (External Agents)

You can distribute agents in separate Python packages and have ftSystem auto-register them via entry points.

## Define an Agent

```python
# my_plugin/agents/ep_agent.py
from ftsystem.agents.base import Agent, AgentConfig

class EPAgent(Agent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def run(self, **kwargs):
        return {"message": "hello from plugin"}
```

## Declare Entry Point (pyproject.toml)

```toml
[project]
name = "ftsystem-my-plugin"
version = "0.1.0"
dependencies = ["ftsystem"]

[project.entry-points."ftsystem.agents"]
EPAgent = "my_plugin.agents.ep_agent:EPAgent"
```

Install the plugin package into the same environment as ftSystem. On startup, ftSystem will import entry points from the group `ftsystem.agents` and register exposed classes that subclass `Agent`.

## Debugging
- List agents: `python -m src.main list-agents --verbose --show-errors`
- Import issues for plugins appear under "Import errors".

