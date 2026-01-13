"""Tests for the CodeAgent."""

import pytest
import os
from langcode.agent import CodeAgent, AgentState
from langcode.tools import read_file, CODE_TOOLS
from langchain_core.messages import HumanMessage


@pytest.fixture
def agent():
    """Create an agent instance for testing."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = CodeAgent(api_key=api_key)
    return agent


def test_agent_initialization():
    """Test agent initialization."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = CodeAgent(api_key=api_key)
    assert agent.llm is not None
    assert agent.tools == {}
    assert agent.graph is None


def test_add_tool(agent):
    """Test adding tools to the agent."""
    agent.add_tool(read_file)
    assert "read_file" in agent.tools
    assert agent.tools["read_file"] == read_file


def test_register_multiple_tools(agent):
    """Test registering multiple tools."""
    agent.register_tools(CODE_TOOLS)
    assert len(agent.tools) > 0
    assert all(tool.name in agent.tools for tool in CODE_TOOLS)


def test_build_graph(agent):
    """Test building the LangGraph graph."""
    agent.register_tools(CODE_TOOLS)
    graph = agent.build_graph()

    assert graph is not None
    assert agent.graph is not None


def test_agent_state_initialization():
    """Test AgentState initialization."""
    state = AgentState(messages=[HumanMessage(content="test")])
    assert len(state.messages) == 1
    assert state.working_directory == "/workspace"
    assert state.tools == {}


@pytest.mark.asyncio
async def test_should_continue_no_tools(agent):
    """Test _should_continue when no tools are needed."""
    agent.register_tools(CODE_TOOLS)

    state = AgentState(
        messages=[HumanMessage(content="Hello")]
    )

    result = agent._should_continue(state)
    assert result == "end"


def test_agent_initialization_with_custom_model():
    """Test initializing agent with custom model."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = CodeAgent(api_key=api_key, model="claude-opus-4-5-20251101")
    assert agent.llm.model_name == "claude-opus-4-5-20251101"
