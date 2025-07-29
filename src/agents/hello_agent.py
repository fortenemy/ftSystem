
# src/agents/hello_agent.py

from agents.base import Agent, AgentConfig
import typer


class HelloAgent(Agent):
    """
    Minimal demonstration agent that prints a greeting.
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def run(self, **kwargs) -> None:  # type: ignore[override]
        typer.echo("Hello, world!")