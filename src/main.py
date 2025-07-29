
# src/main.py

import typer

app = typer.Typer(help="ftSystem – Multi-Agent AI CLI")

@app.command()
def run(agent_name: str):
    """
    Runs the specified agent.
    """
    # TODO: later import and invoke the appropriate agent
    typer.echo(f"Running agent: {agent_name}")

@app.command("list-agents")
def list_agents():
    """
    Displays the list of available agents.
    """
    # TODO: later implement dynamic retrieval of the agents list
    typer.echo("Available agents:\n - hello\n - ...")

if __name__ == "__main__":
    app()