from typing import Any
from .base import Agent, AgentConfig


class ConfigEchoAgent(Agent):
    """Agent that returns its AgentConfig as a serializable dict for testing configs."""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def run(self, **kwargs: Any) -> Any:
        return {
            "name": self.config.name,
            "description": self.config.description,
            "params": self.config.params or {},
        }

