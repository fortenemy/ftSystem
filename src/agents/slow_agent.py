import time
from typing import Any

from .base import Agent, AgentConfig


class SlowAgent(Agent):
    """Simple agent that sleeps to simulate long-running work."""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def run(self, **kwargs: Any) -> Any:
        time.sleep(1.0)
        return "slow"

