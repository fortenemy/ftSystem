from typing import List, Optional

from agents.base import Message


class Forum:
    """
    In-memory forum for orchestration transcripts.
    """

    def __init__(self) -> None:
        """Initialise an empty transcript container."""
        self._messages: List[Message] = []

    def post(self, role: str, content: str, agent: Optional[str] = None) -> Message:
        """Append a message to the transcript and return its Pydantic model."""
        msg = Message(role=role, agent=agent, content=content)
        self._messages.append(msg)
        return msg

    def messages(self) -> List[Message]:
        """Return a shallow copy of accumulated messages."""
        return list(self._messages)

    def to_dict(self) -> List[dict]:
        """Serialise messages to JSON-friendly dictionaries."""
        # JSON-friendly dicts (e.g., datetime -> ISO string)
        return [m.model_dump(mode="json") for m in self._messages]
