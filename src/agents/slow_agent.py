import time
from typing import Any

from .base import Agent, AgentConfig


class SlowAgent(Agent):
    """Simple agent that sleeps to simulate long-running work."""

    def __init__(self, config: AgentConfig):
        """Store configuration for compatibility with the Agent API."""
        super().__init__(config)

    def run(self, **kwargs: Any) -> Any:
        """Sleep for a fixed duration and return a status string."""
        time.sleep(1.0)
        return "slow"
