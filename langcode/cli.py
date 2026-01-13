"""CLI interface for LangCode agent."""

import os
import click
from pathlib import Path
from dotenv import load_dotenv
from langcode.agent import CodeAgent
from langcode.tools import CODE_TOOLS


@click.group()
def cli():
    """LangCode - Claude Code clone built with LangChain and LangGraph."""
    load_dotenv()


@cli.command()
@click.argument("task", nargs=-1, required=False)
@click.option(
    "--dir",
    "-d",
    type=click.Path(exists=True),
    default=".",
    help="Working directory for the agent",
)
@click.option(
    "--model",
    "-m",
    default="claude-opus-4-5-20251101",
    help="Claude model to use",
)
@click.option(
    "--api-key",
    envvar="ANTHROPIC_API_KEY",
    help="Anthropic API key",
)
def run(task, dir, model, api_key):
    """Run the agent on a specific task."""
    if not task:
        # Enter interactive mode
        interactive(dir, model, api_key)
    else:
        task_str = " ".join(task)

        # Initialize agent
        agent = CodeAgent(api_key=api_key, model=model)
        agent.register_tools(CODE_TOOLS)
        agent.build_graph()

        # Run the task
        click.echo(f"Running task: {task_str}")
        click.echo("-" * 50)

        try:
            result = agent.run(task_str, working_directory=dir)
            click.echo("\nAgent Response:")
            click.echo("-" * 50)
            click.echo(result)
        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)


@cli.command()
@click.option(
    "--dir",
    "-d",
    type=click.Path(exists=True),
    default=".",
    help="Working directory for the agent",
)
@click.option(
    "--model",
    "-m",
    default="claude-opus-4-5-20251101",
    help="Claude model to use",
)
@click.option(
    "--api-key",
    envvar="ANTHROPIC_API_KEY",
    help="Anthropic API key",
)
def interactive(dir, model, api_key):
    """Start an interactive session with the agent."""
    if not api_key:
        click.echo("Error: ANTHROPIC_API_KEY not set", err=True)
        raise click.Exit(1)

    # Initialize agent
    agent = CodeAgent(api_key=api_key, model=model)
    agent.register_tools(CODE_TOOLS)
    agent.build_graph()

    click.echo("LangCode Interactive Agent")
    click.echo("=" * 50)
    click.echo(f"Working directory: {dir}")
    click.echo(f"Model: {model}")
    click.echo("Type 'exit' to quit")
    click.echo("=" * 50)

    # Run interactive mode
    agent.run_interactive(working_directory=dir)

    click.echo("\nGoodbye!")


@cli.command()
def version():
    """Show version information."""
    from langcode import __version__

    click.echo(f"LangCode version {__version__}")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
