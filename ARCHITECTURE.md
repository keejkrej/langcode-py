# LangCode Architecture

This document explains the architecture and design patterns used in LangCode.

## High-Level Overview

LangCode is a multi-layered architecture designed to coordinate code understanding and manipulation through an AI agent:

```
┌─────────────────────────────────────────────┐
│           User Interface (CLI)              │
│  Interactive Mode  │  Single Task Mode      │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│         CodeAgent (LangGraph)               │
│  ┌──────────────────────────────────────┐   │
│  │  LLM: Claude API with Tool Binding   │   │
│  │  Graph: State Management & Routing   │   │
│  │  Tools: Registered Tool Invocation   │   │
│  └──────────────────────────────────────┘   │
└────────────────────┬────────────────────────┘
                     │
       ┌─────────────┼─────────────┐
       │             │             │
┌──────▼──┐  ┌──────▼──┐   ┌──────▼──┐
│ Tools   │  │Analyzer │   │ Context │
│ Module  │  │ Module  │   │ Module  │
└─────────┘  └─────────┘   └─────────┘
       │             │             │
       └─────────────┼─────────────┘
                     │
             ┌───────▼────────┐
             │  File System   │
             │  & Python AST  │
             └────────────────┘
```

## Component Architecture

### 1. CLI Layer (`cli.py`)

**Purpose**: Provide user interface for agent interaction

**Key Classes**:
- `cli`: Click command group for CLI entry point
- `run()`: Execute single task
- `interactive()`: Start interactive session
- `version()`: Show version info

**Responsibilities**:
- Parse command-line arguments
- Initialize agent and tools
- Handle user input/output
- Manage working directory context

**Design Pattern**: Command Pattern with Click framework

### 2. Agent Layer (`agent.py`)

**Purpose**: Orchestrate code understanding through LangGraph

**Key Classes**:
- `CodeAgent`: Main agent coordinator
- `AgentState`: State container for execution context

**Key Methods**:
- `add_tool()`: Register individual tool
- `register_tools()`: Register multiple tools
- `build_graph()`: Construct LangGraph workflow
- `run()`: Execute task once
- `run_interactive()`: Interactive conversation loop

**Graph Structure**:
```
START
  │
  ▼
agent (call LLM)
  │
  ├─ has tool calls? ──► tools (execute)
  │                        │
  │◄───────────────────────┘
  │
  └─ no tool calls ─────► END
```

**Design Pattern**: State Machine + Tool Calling Pattern

**Key Design Decisions**:
- **State as Dataclass**: Simple, mutable, type-safe
- **Reducer Pattern**: `add_messages` for conversation history
- **Tool Binding**: LangChain's `bind_tools()` for automatic tool calling
- **Conditional Routing**: LangGraph's `conditional_edges` for branching

### 3. Tools Module (`tools.py`)

**Purpose**: Provide code manipulation capabilities

**Tool Categories**:

#### File Operations
- `read_file()`: Read with optional line ranges
- `write_file()`: Create/overwrite files
- `edit_file()`: Find-and-replace content

#### Directory Operations
- `list_directory()`: Browse file tree

#### Code Search
- `search_code()`: Regex pattern matching

#### Code Analysis
- `analyze_code_structure()`: Python AST parsing

**Design Pattern**: Tool Pattern with Pydantic Schemas

**Schema Pattern**:
```python
@tool(args_schema=InputModel)
def tool_function(params) -> str:
    """Tool description for Claude."""
    return result
```

**Key Insight**: Pydantic schemas are automatically converted to JSON schemas that Claude understands. This enables:
- Type validation
- Clear parameter descriptions
- Automatic UI generation
- Schema documentation

### 4. Analyzer Module (`analyzer.py`)

**Purpose**: Advanced code understanding through AST analysis

**Key Classes**:
- `CodeAnalyzer`: Main analyzer
- `Symbol`: Code entity representation

**Analysis Capabilities**:
- Extract class definitions and methods
- Extract function definitions with signatures
- Track parent-child relationships (methods in classes)
- Extract docstrings and type hints
- Find symbol definitions
- Find symbol references

**Design Pattern**: Visitor Pattern (AST walking)

**Key Data Structure - Symbol**:
```python
@dataclass
class Symbol:
    name: str              # Symbol name
    type: str             # "class", "function", "method", "variable"
    file_path: str        # Location
    line_start: int
    line_end: int
    parent: Optional[str] # Parent class name (for methods)
    docstring: Optional[str]
    arguments: list[str]  # Function arguments
    return_type: Optional[str]  # Type hint
```

**Design Decisions**:
- **AST Over Regex**: More accurate for Python code
- **Caching**: Cache parsed trees to avoid re-parsing
- **Symbol Extraction**: Pre-compute symbols for fast lookup
- **Type Information**: Extract from annotations when available

### 5. Context Module (`context.py`)

**Purpose**: Manage conversation state and memory

**Key Classes**:
- `ConversationContext`: Single conversation state
- `ContextManager`: Multi-session management

**ConversationContext Features**:
- Message history with timestamps
- File buffer cache
- Custom metadata storage
- JSON serialization for persistence

**ContextManager Features**:
- Create multiple conversation contexts
- Save/load from JSON files
- List all saved sessions
- Track current context

**Design Pattern**: Context Pattern + Repository Pattern

**Storage Structure**:
```
.langcode/
├── session1.json  # {"messages": [...], "metadata": {...}}
├── session2.json
└── ...
```

**Key Design Decisions**:
- **Immutable History**: Messages are append-only
- **File Buffer**: Cache files to avoid re-reading
- **Metadata**: Extensible key-value store for session info
- **JSON Persistence**: Human-readable format for debugging

## Data Flow

### Single Task Execution

```
User Input
    │
    ▼
CLI (parse args) → Initialize Agent + Tools
    │
    ▼
Create Initial State
    │
    ├─ messages: [HumanMessage(task)]
    ├─ tools: {tool1, tool2, ...}
    └─ working_directory: specified dir
    │
    ▼
LangGraph Execution
    │
    ├─ Call LLM with tools bound
    │  └─ LLM can request tool use
    │
    ├─ If tool calls needed:
    │  ├─ Extract tool name and args
    │  ├─ Invoke tool with input
    │  └─ Return ToolMessage with result
    │
    ├─ Loop until LLM stops requesting tools
    │
    └─ Return final response
    │
    ▼
Display Result to User
```

### Interactive Conversation

```
CLI → Start interactive loop
    │
    ├─ Read user input
    │
    ├─ Add to message history
    │
    ├─ Create state with all messages
    │
    ├─ Execute LangGraph
    │
    ├─ Display response
    │
    └─ Loop back to "Read user input"
```

## Tool Invocation Flow

```
LLM Output with Tool Call
    │
    ├─ Extract: {name: "read_file", args: {path: "agent.py"}}
    │
    ├─ Lookup tool: tool = tools[name]
    │
    ├─ Invoke: result = tool.invoke(args)
    │
    ├─ Wrap result: ToolMessage(content=str(result), tool_call_id=id)
    │
    └─ Add to state.messages
       │
       └─ Back to LLM
```

## State Management Strategy

### AgentState Dataclass

```python
@dataclass
class AgentState:
    messages: Annotated[list[BaseMessage], add_messages]
    # ^ Pydantic's add_messages reducer handles message merging

    tools: dict[str, BaseTool]        # Registered tools
    working_directory: str             # Context
    task: str                          # Original task
    last_tool_result: Any              # Recent result
```

**Key Feature - add_messages Reducer**:
- Automatically deduplicates consecutive identical messages
- Maintains conversation thread integrity
- Handles message merging across multiple updates

## Tool Schema Pattern

Every tool follows this pattern:

```python
from pydantic import BaseModel, Field

class ToolInput(BaseModel):
    param1: str = Field(description="...")
    param2: int = Field(default=10, description="...")

@tool(args_schema=ToolInput)
def tool_name(param1: str, param2: int = 10) -> str:
    """Tool description for Claude.

    Claude sees this description and docstring.
    """
    return result
```

**Why Pydantic**:
1. Automatic JSON schema generation
2. Type validation and coercion
3. IDE autocomplete support
4. Clear parameter documentation
5. Default value handling

## Extension Points

### Adding a New Tool

```python
@tool(args_schema=InputSchema)
def new_tool(param: str) -> str:
    """Tool description."""
    return result

agent.add_tool(new_tool)
```

### Adding a New Node to Graph

```python
def custom_node(state: AgentState) -> dict:
    # Process state
    return {"messages": [...]}

workflow.add_node("custom", custom_node)
```

### Custom Tool Callback

```python
class CustomTool(BaseTool):
    name = "my_tool"
    description = "..."
    args_schema = InputSchema

    def _run(self, **kwargs) -> str:
        return result
```

## Performance Considerations

### Symbol Caching
- Pre-parse files once, cache AST
- Reuse cache for multiple queries
- Clear cache if files change

### File Buffer
- Cache frequently accessed files
- Avoid re-reading same file
- Clear buffer periodically

### Message History
- Keep recent messages for context
- Summarize old messages if too long
- Persist to disk for recovery

## Security Considerations

### Input Validation
- Pydantic validates all tool inputs
- Type checking prevents injection
- File paths bounded to working directory

### Tool Restrictions
- Tools only modify within working directory
- Read-only file system not enforced
- Regex patterns are user-supplied

### API Security
- API key stored in environment variables
- No credentials logged
- Messages don't contain sensitive data by default

## Testing Architecture

### Test Organization
```
tests/
├── test_agent.py       # Agent initialization and graph building
├── test_tools.py       # Individual tool functionality
├── test_analyzer.py    # Symbol analysis and extraction
├── test_context.py     # State and memory management
├── conftest.py         # Pytest fixtures and configuration
└── __init__.py
```

### Test Patterns
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test tool execution in context
- **Fixtures**: Reusable test data (Python code examples, temp files)
- **Mocking**: Mock LLM for deterministic tests

## Dependency Graph

```
cli.py
  ├─ agent.py
  │  ├─ langchain (BaseMessage, tools, etc)
  │  └─ langgraph (StateGraph, workflow)
  │
  ├─ tools.py
  │  ├─ langchain_core.tools (@tool)
  │  ├─ pydantic (schemas)
  │  └─ pathlib (file operations)
  │
  └─ context.py
     ├─ dataclasses
     ├─ pathlib
     └─ json
```

## Future Architecture Improvements

1. **Plugin System**: Allow loading custom tools dynamically
2. **Memory Management**: Implement hierarchical memory for large codebases
3. **Async Tools**: Support concurrent tool execution
4. **Tool Composition**: Chain tools into higher-level operations
5. **Code Generation**: Add code generation tools with validation
6. **Multi-Language Support**: Extend analyzer for other languages
7. **Performance**: Add indexing for fast symbol lookup
8. **Caching**: Implement LRU cache for analysis results

## Design Philosophy

LangCode follows these principles:

1. **Simplicity First**: Start simple, add complexity as needed
2. **Type Safety**: Use type hints and Pydantic throughout
3. **Separation of Concerns**: Each module has single responsibility
4. **Composability**: Tools and components work independently
5. **Extensibility**: Easy to add new tools and nodes
6. **Debuggability**: Clear state transitions and logging
7. **Documentation**: Code is self-documenting with clear comments
