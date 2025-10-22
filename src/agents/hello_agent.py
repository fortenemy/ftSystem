
import logging
from .base import Agent, AgentConfig
from typing import Any

class HelloAgent(Agent):
    """
    Minimal demonstration agent that prints a greeting.
    """
    def __init__(self, config: AgentConfig):
        """Store configuration for interface parity with other agents."""
        super().__init__(config)

    def run(self, **kwargs: Any) -> str:
        """Log a static greeting and return it for downstream consumers."""
        message = "Hello, world!"
        logging.info(message)
        return message
