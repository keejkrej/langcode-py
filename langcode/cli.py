"""CLI interface for LangCode agent."""

import os
import click
from pathlib import Path
from dotenv import load_dotenv
from langcode.agent import CodeAgent, StreamingCallback
from langcode.tools import ALL_TOOLS


# Mode configurations
MODES = {
    "normal": {
        "description": "Standard mode with confirmation prompts",
        "auto_execute": False,
        "show_plan": True,
        "require_confirmation": True,
    },
    "plan": {
        "description": "Planning mode - shows plan before execution",
        "auto_execute": False,
        "show_plan": True,
        "require_confirmation": True,
    },
    "yolo": {
        "description": "YOLO mode - auto-executes without confirmation",
        "auto_execute": True,
        "show_plan": False,
        "require_confirmation": False,
    },
    "build": {
        "description": "Build mode - focused on code generation and testing",
        "auto_execute": True,
        "show_plan": True,
        "require_confirmation": False,
    },
}


class ModeManager:
    """Manages agent execution modes."""

    def __init__(self, initial_mode: str = "normal"):
        self.current_mode = initial_mode
        self.mode_config = MODES.get(initial_mode, MODES["normal"])

    def switch_mode(self, mode: str) -> bool:
        """Switch to a different mode."""
        if mode in MODES:
            self.current_mode = mode
            self.mode_config = MODES[mode]
            return True
        return False

    def get_mode_info(self) -> str:
        """Get current mode information."""
        return f"Mode: {self.current_mode} - {self.mode_config['description']}"

    def list_modes(self) -> str:
        """List all available modes."""
        lines = ["Available modes:"]
        for name, config in MODES.items():
            marker = "→ " if name == self.current_mode else "  "
            lines.append(f"{marker}{name}: {config['description']}")
        return "\n".join(lines)

    @property
    def auto_execute(self) -> bool:
        return self.mode_config["auto_execute"]

    @property
    def show_plan(self) -> bool:
        return self.mode_config["show_plan"]

    @property
    def require_confirmation(self) -> bool:
        return self.mode_config["require_confirmation"]


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
@click.option(
    "--mode",
    type=click.Choice(list(MODES.keys())),
    default="normal",
    help="Execution mode",
)
@click.option(
    "--streaming/--no-streaming",
    default=True,
    help="Enable streaming output",
)
def run(task, dir, model, api_key, mode, streaming):
    """Run the agent on a specific task."""
    if not task:
        # Enter interactive mode with the specified mode
        ctx = click.get_current_context()
        ctx.invoke(interactive, dir=dir, model=model, api_key=api_key, mode=mode, streaming=streaming)
    else:
        task_str = " ".join(task)

        # Initialize agent
        agent = CodeAgent(api_key=api_key, model=model, streaming=streaming)
        agent.register_tools(ALL_TOOLS)
        agent.build_graph()

        mode_manager = ModeManager(mode)

        # Run the task
        click.echo(f"Running task: {task_str}")
        click.echo(f"{mode_manager.get_mode_info()}")
        click.echo("-" * 50)

        try:
            if streaming:
                result = agent.run_streaming(task_str, working_directory=dir)
            else:
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
@click.option(
    "--mode",
    type=click.Choice(list(MODES.keys())),
    default="normal",
    help="Initial execution mode",
)
@click.option(
    "--streaming/--no-streaming",
    default=True,
    help="Enable streaming output",
)
def interactive(dir, model, api_key, mode, streaming):
    """Start an interactive session with the agent."""
    if not api_key:
        click.echo("Error: ANTHROPIC_API_KEY not set", err=True)
        raise click.Exit(1)

    # Initialize agent
    agent = CodeAgent(api_key=api_key, model=model, streaming=streaming)
    agent.register_tools(ALL_TOOLS)
    agent.build_graph()

    mode_manager = ModeManager(mode)

    click.echo("LangCode Interactive Agent")
    click.echo("=" * 50)
    click.echo(f"Working directory: {dir}")
    click.echo(f"Model: {model}")
    click.echo(f"{mode_manager.get_mode_info()}")
    click.echo("")
    click.echo("Commands:")
    click.echo("  /mode <name>  - Switch mode (normal, plan, yolo, build)")
    click.echo("  /modes        - List all modes")
    click.echo("  /status       - Show current status")
    click.echo("  exit          - Quit")
    click.echo("=" * 50)

    messages = []

    while True:
        try:
            user_input = input("\n> ").strip()

            if user_input.lower() == "exit":
                break

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                parts = user_input[1:].split(maxsplit=1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                if cmd == "mode":
                    if args:
                        if mode_manager.switch_mode(args):
                            click.echo(f"Switched to {mode_manager.get_mode_info()}")
                        else:
                            click.echo(f"Unknown mode: {args}")
                            click.echo(mode_manager.list_modes())
                    else:
                        click.echo(mode_manager.get_mode_info())
                elif cmd == "modes":
                    click.echo(mode_manager.list_modes())
                elif cmd == "status":
                    click.echo(f"Working directory: {dir}")
                    click.echo(f"Model: {model}")
                    click.echo(f"{mode_manager.get_mode_info()}")
                    click.echo(f"Messages in history: {len(messages)}")
                else:
                    click.echo(f"Unknown command: /{cmd}")
                continue

            # Process with agent
            from langchain_core.messages import HumanMessage

            messages.append(HumanMessage(content=user_input))

            from langcode.agent import AgentState

            state = AgentState(
                messages=messages,
                tools=agent.tools,
                working_directory=dir,
                task=user_input,
            )

            result = agent.graph.invoke(state)
            messages = result["messages"]

            # Print the last response
            from langchain_core.messages import ToolMessage

            for msg in reversed(result["messages"]):
                if hasattr(msg, "content") and msg.content and not isinstance(msg, ToolMessage):
                    click.echo(f"\nAgent: {msg.content}")
                    break

        except KeyboardInterrupt:
            break
        except Exception as e:
            click.echo(f"Error: {e}")

    click.echo("\nGoodbye!")


@cli.command()
def version():
    """Show version information."""
    from langcode import __version__

    click.echo(f"LangCode version {__version__}")


@cli.command()
def modes():
    """List all available execution modes."""
    click.echo("Available execution modes:")
    click.echo("")
    for name, config in MODES.items():
        click.echo(f"  {name}:")
        click.echo(f"    {config['description']}")
        click.echo(f"    Auto-execute: {config['auto_execute']}")
        click.echo(f"    Show plan: {config['show_plan']}")
        click.echo(f"    Require confirmation: {config['require_confirmation']}")
        click.echo("")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
