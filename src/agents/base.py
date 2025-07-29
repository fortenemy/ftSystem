
# src/agents/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """
    Common configuration for every agent.
    Extend this model in each concrete agent when you need extra fields.
    """
    name: str = Field(..., description="Unique agent name")
    description: str = Field("", description="Short description of the agent")


class Agent(ABC):
    """
    Abstract base class for ftSystem agents.
    """

    def __init__(self, config: AgentConfig) -> None:
        self.config = config

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """
        Execute the agent's main task.

        Concrete agents must implement this method.
        """
        raise NotImplementedError