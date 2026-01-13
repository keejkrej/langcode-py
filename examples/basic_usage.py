"""Basic usage examples for LangCode agent."""

import os
from langcode.agent import CodeAgent
from langcode.tools import CODE_TOOLS
from langcode.analyzer import ANALYZER_TOOLS

# Set up API key
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable not set")


def example_1_analyze_file():
    """Example 1: Analyze code structure."""
    print("\n=== Example 1: Analyze File Structure ===")

    agent = CodeAgent(api_key=api_key)
    agent.register_tools(CODE_TOOLS + ANALYZER_TOOLS)
    agent.build_graph()

    task = "Read the file langcode/agent.py and tell me about the CodeAgent class"
    result = agent.run(task, working_directory="/Users/jack/workspace/langcode-project/langcode-py-init")

    print(f"Task: {task}")
    print(f"Result:\n{result}")


def example_2_search_code():
    """Example 2: Search for code patterns."""
    print("\n=== Example 2: Search Code ===")

    agent = CodeAgent(api_key=api_key)
    agent.register_tools(CODE_TOOLS)
    agent.build_graph()

    task = "Search for all references to 'def ' in the langcode directory and tell me how many functions exist"
    result = agent.run(
        task, working_directory="/Users/jack/workspace/langcode-project/langcode-py-init"
    )

    print(f"Task: {task}")
    print(f"Result:\n{result}")


def example_3_find_symbol():
    """Example 3: Find and analyze a symbol."""
    print("\n=== Example 3: Find Symbol ===")

    agent = CodeAgent(api_key=api_key)
    agent.register_tools(CODE_TOOLS + ANALYZER_TOOLS)
    agent.build_graph()

    task = "Find the CodeAgent class definition and tell me all its methods"
    result = agent.run(
        task, working_directory="/Users/jack/workspace/langcode-project/langcode-py-init"
    )

    print(f"Task: {task}")
    print(f"Result:\n{result}")


def example_4_directory_listing():
    """Example 4: Explore directory structure."""
    print("\n=== Example 4: Directory Listing ===")

    agent = CodeAgent(api_key=api_key)
    agent.register_tools(CODE_TOOLS)
    agent.build_graph()

    task = "List the contents of the langcode directory recursively and tell me about the project structure"
    result = agent.run(
        task, working_directory="/Users/jack/workspace/langcode-project/langcode-py-init"
    )

    print(f"Task: {task}")
    print(f"Result:\n{result}")


if __name__ == "__main__":
    print("LangCode Basic Usage Examples")
    print("=" * 50)

    # Uncomment examples to run
    # example_1_analyze_file()
    # example_2_search_code()
    # example_3_find_symbol()
    # example_4_directory_listing()

    print("\nTo run examples, uncomment them in the script")
