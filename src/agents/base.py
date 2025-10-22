
# src/agents/base.py

from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any, Dict, Union, List, Optional, Literal
from datetime import datetime, timezone

class AgentConfig(BaseModel):
    """
    Base configuration model for an agent.
    All agent configurations should inherit from this class.
    """
    name: str
    description: str
    params: Optional[Dict[str, Any]] = None

class Agent(ABC):
    """
    Abstract base class for all agents in the system.
    """
    def __init__(self, config: AgentConfig):
        self.config = config

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """
        Execute the agent's main task.

        Concrete agents must implement this method.
        """
        pass


# JSON-like type alias for agent results
JSONLike = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


class RunResult(BaseModel):
    """
    Standardized result container for agents.
    """
    status: str  # e.g., "ok" | "error"
    message: Optional[str] = None
    data: Optional[JSONLike] = None
    metrics: Optional[Dict[str, float]] = None


class SessionSummary(BaseModel):
    """
    Persistent session summary for long-term memory.
    """
    timestamp: datetime
    agent: str
    status: str
    message: Optional[str] = None
    data_preview: Optional[str] = None
    tags: Optional[list[str]] = None


class Message(BaseModel):
    """
    Forum message used in orchestration transcripts.
    """
    role: Literal["system", "user", "agent"]
    agent: Optional[str] = None
    content: str
    timestamp: datetime = datetime.now(timezone.utc)
