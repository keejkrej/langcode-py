# LangCode Quick Start Guide

Welcome to LangCode! This guide will get you up and running in 5 minutes.

## Prerequisites

- Python 3.11+
- Anthropic API key (get one at https://console.anthropic.com)

## Installation

1. **Clone and navigate to the project:**
   ```bash
   cd /path/to/langcode-py-init
   ```

2. **Set up environment:**
   ```bash
   # Copy the example env file
   cp .env.example .env

   # Edit .env and add your API key
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

3. **Install the package:**
   ```bash
   pip install -e .
   ```

4. **Verify installation:**
   ```bash
   langcode version
   ```

## Basic Usage

### Interactive Mode

Start an interactive conversation with the agent:

```bash
langcode interactive --dir .
```

Then try these commands:

```
> List the files in the langcode directory
> What's in the agent.py file?
> Find the CodeAgent class and tell me its methods
> Search for all functions that use 'async'
> exit
```

### Single Task Mode

Run a specific task:

```bash
# Analyze code structure
langcode run "Analyze the project structure and tell me what each module does"

# Find code patterns
langcode run "Find all classes in the langcode directory"

# Get help with specific code
langcode run "Explain what the AgentState class does"
```

## Project Structure

```
langcode/                 # Main package
├── agent.py            # Core LangGraph agent
├── tools.py            # Code manipulation tools
├── analyzer.py         # Code analysis and symbol finding
├── context.py          # Conversation memory management
├── cli.py              # Command-line interface
└── __init__.py

tests/                   # Comprehensive test suite
├── test_agent.py
├── test_analyzer.py
├── test_context.py
├── test_tools.py
└── conftest.py

examples/                # Usage examples
└── basic_usage.py
```

## Key Capabilities

### File Operations
- Read files with optional line ranges
- Write and create new files
- Edit specific content within files
- List and explore directories

### Code Analysis
- Parse Python code structure (classes, functions, methods)
- Find symbol definitions
- Locate all references to a symbol
- Extract function signatures and docstrings

### Conversation Management
- Maintain persistent conversation history
- Cache file contents for efficient re-use
- Store and retrieve session contexts
- Add custom metadata to sessions

## Common Tasks

### Example 1: Understand a Module

```bash
langcode run "Read langcode/agent.py and explain the CodeAgent class and its main methods"
```

### Example 2: Find Code Issues

```bash
langcode run "Search for all TODO comments in the langcode directory"
```

### Example 3: Analyze Dependencies

```bash
langcode run "Find all imports in langcode/agent.py and tell me what external libraries are used"
```

### Example 4: Create a New File

```bash
langcode run "Create a new file called 'config.py' with a Config dataclass that has working_directory and model_name fields"
```

## Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=langcode

# Run specific test file
pytest tests/test_agent.py
```

## Troubleshooting

**"ANTHROPIC_API_KEY not set"**
- Make sure you've set the environment variable or created a `.env` file with your key

**"ModuleNotFoundError"**
- Run `pip install -e .` to install the package in editable mode

**"Connection error"**
- Check your internet connection and API key validity
- Try again - sometimes the API has temporary issues

**Tests failing**
- Make sure you have `ANTHROPIC_API_KEY` set for integration tests
- Run `pip install -e ".[dev]"` to ensure all dependencies are installed

## Next Steps

1. **Explore Examples**: Check `examples/basic_usage.py` for code examples
2. **Read the Docs**: See `README.md` for comprehensive documentation
3. **Customize Tools**: Add custom tools in `langcode/tools.py`
4. **Extend Agent**: Customize the agent in `langcode/agent.py`
5. **Build Features**: Create new capabilities tailored to your needs

## Tips

- **Interactive Mode**: Best for exploration and learning
- **Single Task Mode**: Better for automation and scripting
- **Context Management**: Use sessions to maintain state across multiple tasks
- **Tool Selection**: The agent automatically chooses relevant tools for tasks
- **File Caching**: Large files are cached to reduce API calls

## API Rate Limits

LangCode uses the Claude API. Be mindful of:
- Rate limits (varies by plan)
- Token usage (charged per API call)
- Concurrent request limits

For production use, consider:
- Implementing caching strategies
- Batching operations
- Monitoring token usage
- Setting up error handling and retries

## Support

For issues and questions:
1. Check the README.md for more details
2. Review test examples in `tests/`
3. Check if your issue is in the Troubleshooting section above
4. Review the code comments in the source files

Enjoy using LangCode!
