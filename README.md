# LangCode - Claude Code Clone

A Claude Code/OpenCode clone built with LangChain and LangGraph in Python. This project demonstrates how to build an AI-powered code agent that can understand, analyze, and manipulate code using the Claude API.

## Features

- **Agent Framework**: Built with LangGraph for sophisticated multi-step reasoning
- **Code Tools**: File operations, code search, and analysis capabilities
- **Interactive CLI**: Command-line interface for both single tasks and interactive sessions
- **Symbol Analysis**: Find and analyze code symbols (classes, functions, methods)
- **Context Management**: Persistent conversation history and session management
- **Extensible Tool System**: Easy to add new tools for code manipulation

## Architecture

```
langcode/
├── agent.py          # Core LangGraph agent framework
├── tools.py          # Basic code manipulation tools
├── analyzer.py       # Advanced code analysis and symbol finding
├── context.py        # Conversation state and memory management
├── cli.py           # Command-line interface
└── __init__.py      # Package initialization
```

### Core Components

**Agent (agent.py)**
- `CodeAgent`: Main agent class orchestrating LangChain and LangGraph
- `AgentState`: Dataclass managing agent state throughout execution
- Uses LangGraph's StateGraph for workflow management

**Tools (tools.py)**
- `read_file`: Read file contents with optional line ranges
- `write_file`: Create or overwrite files
- `edit_file`: Replace specific content in files
- `list_directory`: Browse directory structures
- `search_code`: Find patterns using regex
- `analyze_code_structure`: Parse Python AST for structure analysis

**Analyzer (analyzer.py)**
- `CodeAnalyzer`: Advanced analysis for symbol extraction
- `find_symbol`: Locate classes, functions, and methods
- `find_references`: Locate all uses of a symbol
- `Symbol`: Data structure representing code entities

**Context (context.py)**
- `ConversationContext`: Manages single conversation state
- `ContextManager`: Handles multiple conversation sessions
- Persistence to JSON for session continuity

## Installation

```bash
# Install the package
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

## Configuration

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Or create a `.env` file:

```
ANTHROPIC_API_KEY=your-api-key-here
```

## Usage

### Interactive Mode

Start an interactive session:

```bash
langcode interactive --dir /path/to/code
```

Example session:
```
> Read the file langcode/agent.py
> What are the main methods of CodeAgent?
> Find all references to AgentState
> exit
```

### Single Task Mode

Run a single task:

```bash
langcode run "Analyze the project structure"
langcode run "Find the function named 'foo' and show its references"
langcode run "Create a new test file for the analyzer"
```

### Version

```bash
langcode version
```

## Implementation Details

### LangGraph Workflow

The agent uses a simple but effective LangGraph workflow:

```
START → agent → should_continue? → tools → agent → END
                         ↓
                    (no tools needed)
```

1. **agent node**: Calls Claude API with current messages
2. **should_continue**: Checks if model requested tool use
3. **tools node**: Executes requested tools and returns results
4. Loop continues until model doesn't request more tools

### Tool Integration

Tools are integrated through LangChain's tool binding mechanism:

```python
# Register tools with the agent
agent.register_tools([read_file, write_file, search_code, ...])

# LLM automatically gains tool-calling capability
agent.llm.bind_tools(list(agent.tools.values()))
```

### State Management

The `AgentState` dataclass uses Pydantic's `add_messages` reducer for conversation memory:

```python
messages: Annotated[list[BaseMessage], add_messages]
```

This ensures messages are properly accumulated across multiple tool calls.

## Example Implementations

### Reading and Analyzing Code

```
Task: "Find the CodeAgent class and explain its main methods"

1. Agent calls find_symbol("CodeAgent")
2. Agent calls read_file(path) with result
3. Agent analyzes structure and provides explanation
```

### Making Code Changes

```
Task: "Add a new method called 'debug_mode' to CodeAgent"

1. Agent calls read_file() to get current content
2. Agent calls find_symbol("CodeAgent") for location
3. Agent calls edit_file() to add the method
4. Agent calls analyze_code_structure() to verify changes
```

### Project Navigation

```
Task: "List all Python files in the project and their structure"

1. Agent calls list_directory() recursively
2. Agent calls analyze_code_structure() for each file
3. Agent compiles a report of project structure
```

## Key Design Decisions

**Why LangGraph?**
- Explicit control flow for code-related tasks
- Easy to add branching logic for complex workflows
- Strong state management for conversation history
- Composable with other LangChain components

**Why Pydantic for Tool Schemas?**
- Claude's tool use API requires JSON schemas
- Pydantic provides validation and serialization
- Type hints enable better IDE support
- Schema generation is automatic

**Simple vs. Advanced Analysis?**
- Basic tools use regex and simple parsing
- Advanced tools use Python AST for semantic understanding
- Users can start simple and add complexity as needed
- Analyzer is decoupled from core agent

## Extending LangCode

### Adding New Tools

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    param1: str = Field(description="Description")
    param2: int = Field(default=10)

@tool(args_schema=MyToolInput)
def my_tool(param1: str, param2: int = 10) -> str:
    """Tool description for the model."""
    return f"Result: {param1} {param2}"

# Register with agent
agent.add_tool(my_tool)
```

### Custom Workflow Nodes

```python
def custom_node(state: AgentState) -> dict:
    """Custom processing step."""
    # Do something with state
    return {"messages": [...]}

workflow.add_node("custom", custom_node)
```

### Advanced Context Features

```python
# Track metadata
context.set_metadata("current_file", "agent.py")

# Cache files to avoid rereading
context.cache_file(path, content)

# Access conversation history
history = context.get_message_history(limit=10)
```

## Limitations

- Currently optimized for Python code analysis
- Symbol analysis limited to Python AST
- No multi-file refactoring support yet
- No version control integration

## Future Enhancements

- Support for multiple programming languages (TypeScript, Go, Rust, etc.)
- Git integration for diffs and commits
- Code generation with testing
- Performance optimization for large codebases
- Plugin system for domain-specific tools
- Web UI for interactive code exploration

## Development

Run tests:

```bash
pytest tests/
```

Code formatting:

```bash
black langcode/
ruff check langcode/
```

## License

MIT

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.
