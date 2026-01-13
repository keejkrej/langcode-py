"""Core agent framework using LangGraph for coordinating code understanding and manipulation."""

from typing import Any, Annotated, Generator, Callable, Optional
from dataclasses import dataclass, field
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessageChunk
from langchain_core.tools import BaseTool
import json
import sys


@dataclass
class AgentState:
    """State managed by the agent throughout execution."""
    messages: Annotated[list[BaseMessage], add_messages]
    tools: dict[str, BaseTool] = field(default_factory=dict)
    working_directory: str = "/workspace"
    task: str = ""
    last_tool_result: Any = None


class StreamingCallback:
    """Callback for handling streaming output."""

    def __init__(self, output_func: Callable[[str], None] = None):
        """Initialize with optional custom output function."""
        self.output_func = output_func or (lambda x: print(x, end="", flush=True))
        self.buffer = []

    def on_token(self, token: str):
        """Handle a streaming token."""
        self.buffer.append(token)
        self.output_func(token)

    def on_tool_start(self, tool_name: str, tool_input: dict):
        """Handle tool start event."""
        self.output_func(f"\n[Using tool: {tool_name}]\n")

    def on_tool_end(self, tool_name: str, output: str):
        """Handle tool end event."""
        # Truncate long outputs for display
        display_output = output[:500] + "..." if len(output) > 500 else output
        self.output_func(f"[Tool result: {display_output}]\n")

    def get_content(self) -> str:
        """Get all buffered content."""
        return "".join(self.buffer)

    def clear(self):
        """Clear the buffer."""
        self.buffer.clear()


class CodeAgent:
    """Main agent for Claude Code/OpenCode clone functionality."""

    def __init__(
        self,
        api_key: str = None,
        model: str = "claude-opus-4-5-20251101",
        streaming: bool = False,
        streaming_callback: Optional[StreamingCallback] = None
    ):
        """Initialize the agent with LangChain and LangGraph.

        Args:
            api_key: Anthropic API key
            model: Model name to use
            streaming: Whether to enable streaming output
            streaming_callback: Optional custom streaming callback
        """
        self.streaming = streaming
        self.streaming_callback = streaming_callback or StreamingCallback()

        self.llm = ChatAnthropic(
            api_key=api_key,
            model=model,
            temperature=0.1,
            streaming=streaming,
        )
        self.tools: dict[str, BaseTool] = {}
        self.graph = None

    def add_tool(self, tool: BaseTool):
        """Register a tool for the agent to use."""
        self.tools[tool.name] = tool
        # Bind tools to LLM
        self.llm = self.llm.bind_tools(list(self.tools.values()))

    def register_tools(self, tools: list[BaseTool]):
        """Register multiple tools at once."""
        for tool in tools:
            self.add_tool(tool)

    def _should_continue(self, state: AgentState) -> str:
        """Determine if agent should continue or end."""
        last_message = state.messages[-1]

        # Check if there are tool calls
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        return "end"

    def _call_model(self, state: AgentState) -> dict:
        """Call the Claude model with current state."""
        response = self.llm.invoke(state.messages)
        return {"messages": [response]}

    def _process_tool_calls(self, state: AgentState) -> dict:
        """Process tool calls from the model response."""
        last_message = state.messages[-1]
        tool_results = []

        if hasattr(last_message, "tool_calls"):
            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_input = tool_call["args"]

                if tool_name in self.tools:
                    tool = self.tools[tool_name]
                    result = tool.invoke(tool_input)
                    tool_results.append(
                        ToolMessage(
                            content=str(result),
                            tool_call_id=tool_call["id"],
                            name=tool_name,
                        )
                    )

        return {"messages": tool_results}

    def build_graph(self) -> StateGraph:
        """Build the LangGraph computation graph."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", ToolNode(self.tools.values()))

        # Add edges
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", self._should_continue)
        workflow.add_edge("tools", "agent")
        workflow.add_edge("agent", END)

        self.graph = workflow.compile()
        return self.graph

    def run(self, task: str, working_directory: str = "/workspace") -> str:
        """Run the agent on a given task."""
        if not self.graph:
            self.build_graph()

        initial_state = AgentState(
            messages=[HumanMessage(content=task)],
            tools=self.tools,
            working_directory=working_directory,
            task=task,
        )

        result = self.graph.invoke(initial_state)

        # Return the last message from the agent
        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and msg.content:
                return msg.content

        return "No response generated"

    def run_streaming(
        self,
        task: str,
        working_directory: str = "/workspace",
        callback: Optional[StreamingCallback] = None
    ) -> str:
        """Run the agent with streaming output.

        Args:
            task: The task to perform
            working_directory: Working directory for file operations
            callback: Optional streaming callback (uses default if not provided)

        Returns:
            The final response content
        """
        if not self.graph:
            self.build_graph()

        cb = callback or self.streaming_callback
        cb.clear()

        initial_state = AgentState(
            messages=[HumanMessage(content=task)],
            tools=self.tools,
            working_directory=working_directory,
            task=task,
        )

        # Stream the graph execution
        final_response = ""
        for event in self.graph.stream(initial_state, stream_mode="updates"):
            for node_name, node_output in event.items():
                if node_name == "agent" and "messages" in node_output:
                    for msg in node_output["messages"]:
                        if hasattr(msg, "content") and msg.content:
                            cb.on_token(msg.content)
                            final_response = msg.content
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                cb.on_tool_start(tool_call["name"], tool_call["args"])
                elif node_name == "tools" and "messages" in node_output:
                    for msg in node_output["messages"]:
                        if isinstance(msg, ToolMessage):
                            cb.on_tool_end(msg.name, msg.content)

        return final_response or cb.get_content()

    def run_interactive(self, working_directory: str = "/workspace"):
        """Run the agent in interactive mode for continuous conversation."""
        if not self.graph:
            self.build_graph()

        messages = []

        print("LangCode Agent started. Type 'exit' to quit.")
        print("-" * 50)

        while True:
            try:
                user_input = input("\n> ").strip()
                if user_input.lower() == "exit":
                    break

                if not user_input:
                    continue

                messages.append(HumanMessage(content=user_input))

                state = AgentState(
                    messages=messages,
                    tools=self.tools,
                    working_directory=working_directory,
                    task=user_input,
                )

                result = self.graph.invoke(state)
                messages = result["messages"]

                # Print the last response
                for msg in reversed(result["messages"]):
                    if hasattr(msg, "content") and msg.content and not isinstance(msg, ToolMessage):
                        print(f"\nAgent: {msg.content}")
                        break

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
