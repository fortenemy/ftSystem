
import logging
from .base import Agent, AgentConfig
from typing import Any

class HelloAgent(Agent):
    """
    Minimal demonstration agent that prints a greeting.
    """
    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def run(self, **kwargs: Any) -> Any:
        """Logs a message and returns it."""
        message = "Hello, world!"
        logging.info(message)
        return message
