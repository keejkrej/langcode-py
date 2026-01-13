"""LangCode - A Claude Code clone built with LangChain and LangGraph."""

__version__ = "0.1.0"

from langcode.agent import CodeAgent, AgentState, StreamingCallback
from langcode.tools import (
    CODE_TOOLS,
    GIT_TOOLS,
    UTIL_TOOLS,
    ALL_TOOLS,
    read_file,
    write_file,
    edit_file,
    list_directory,
    search_code,
    analyze_code_structure,
    git_status,
    git_diff,
    git_log,
    run_bash,
    file_diff,
)
from langcode.analyzer import CodeAnalyzer, Symbol, ANALYZER_TOOLS
from langcode.context import ConversationContext, ContextManager
from langcode.cli import MODES, ModeManager

__all__ = [
    # Version
    "__version__",
    # Agent
    "CodeAgent",
    "AgentState",
    "StreamingCallback",
    # Tool collections
    "CODE_TOOLS",
    "GIT_TOOLS",
    "UTIL_TOOLS",
    "ALL_TOOLS",
    "ANALYZER_TOOLS",
    # Individual tools
    "read_file",
    "write_file",
    "edit_file",
    "list_directory",
    "search_code",
    "analyze_code_structure",
    "git_status",
    "git_diff",
    "git_log",
    "run_bash",
    "file_diff",
    # Analyzer
    "CodeAnalyzer",
    "Symbol",
    # Context
    "ConversationContext",
    "ContextManager",
    # Modes
    "MODES",
    "ModeManager",
]
