"""Tool definitions for code inspection and manipulation."""

import os
from typing import Any
from pathlib import Path
import ast
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class FileReadInput(BaseModel):
    """Input for reading a file."""
    path: str = Field(description="The file path to read")
    start_line: int = Field(default=None, description="Optional start line number (1-indexed)")
    end_line: int = Field(default=None, description="Optional end line number (1-indexed)")


class FileWriteInput(BaseModel):
    """Input for writing to a file."""
    path: str = Field(description="The file path to write to")
    content: str = Field(description="The content to write")


class FileEditInput(BaseModel):
    """Input for editing a file."""
    path: str = Field(description="The file path to edit")
    old_content: str = Field(description="The content to replace")
    new_content: str = Field(description="The new content")


class FileListInput(BaseModel):
    """Input for listing directory contents."""
    path: str = Field(default=".", description="The directory path to list")
    recursive: bool = Field(default=False, description="Whether to list recursively")


class CodeSearchInput(BaseModel):
    """Input for searching code patterns."""
    pattern: str = Field(description="The pattern to search for (regex)")
    path: str = Field(default=".", description="The path to search in")
    file_type: str = Field(default=None, description="Optional file type filter (e.g., 'py', 'js')")


class CodeAnalysisInput(BaseModel):
    """Input for analyzing code structure."""
    path: str = Field(description="The file path to analyze")


@tool(args_schema=FileReadInput)
def read_file(path: str, start_line: int = None, end_line: int = None) -> str:
    """Read a file or portion of a file.

    Args:
        path: File path to read
        start_line: Optional starting line (1-indexed)
        end_line: Optional ending line (1-indexed)

    Returns:
        File contents
    """
    try:
        file_path = Path(path)
        if not file_path.exists():
            return f"Error: File not found: {path}"

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if start_line or end_line:
            lines = content.split("\n")
            start = (start_line - 1) if start_line else 0
            end = end_line if end_line else len(lines)
            content = "\n".join(lines[start:end])

        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool(args_schema=FileWriteInput)
def write_file(path: str, content: str) -> str:
    """Write content to a file, creating it if it doesn't exist.

    Args:
        path: File path to write to
        content: Content to write

    Returns:
        Success or error message
    """
    try:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@tool(args_schema=FileEditInput)
def edit_file(path: str, old_content: str, new_content: str) -> str:
    """Edit a file by replacing specific content.

    Args:
        path: File path to edit
        old_content: The content to find and replace
        new_content: The new content

    Returns:
        Success or error message
    """
    try:
        file_path = Path(path)
        if not file_path.exists():
            return f"Error: File not found: {path}"

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_content not in content:
            return f"Error: Content to replace not found in {path}"

        new_file_content = content.replace(old_content, new_content, 1)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_file_content)

        return f"Successfully edited {path}"
    except Exception as e:
        return f"Error editing file: {str(e)}"


@tool(args_schema=FileListInput)
def list_directory(path: str = ".", recursive: bool = False) -> str:
    """List contents of a directory.

    Args:
        path: Directory path to list
        recursive: Whether to list recursively

    Returns:
        Directory listing
    """
    try:
        dir_path = Path(path)
        if not dir_path.exists():
            return f"Error: Directory not found: {path}"

        def format_tree(p: Path, prefix: str = "", is_last: bool = True) -> list[str]:
            """Format directory tree."""
            lines = []

            try:
                entries = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            except PermissionError:
                return lines

            for i, entry in enumerate(entries):
                is_last_entry = i == len(entries) - 1
                current_prefix = "└── " if is_last_entry else "├── "
                lines.append(f"{prefix}{current_prefix}{entry.name}")

                if entry.is_dir() and recursive:
                    extension = "    " if is_last_entry else "│   "
                    lines.extend(format_tree(entry, prefix + extension, is_last_entry))

            return lines

        result = [str(dir_path)]
        result.extend(format_tree(dir_path))
        return "\n".join(result)
    except Exception as e:
        return f"Error listing directory: {str(e)}"


@tool(args_schema=CodeSearchInput)
def search_code(pattern: str, path: str = ".", file_type: str = None) -> str:
    """Search for patterns in code files.

    Args:
        pattern: Regex pattern to search for
        path: Directory to search in
        file_type: Optional file extension filter

    Returns:
        Search results
    """
    import re

    try:
        search_path = Path(path)
        if not search_path.exists():
            return f"Error: Path not found: {path}"

        pattern_re = re.compile(pattern)
        results = []

        for file_path in search_path.rglob("*"):
            if not file_path.is_file():
                continue

            # Skip non-code files
            if file_path.name.startswith("."):
                continue

            if file_type and not file_path.suffix.endswith(file_type):
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern_re.search(line):
                            results.append(f"{file_path}:{line_num}: {line.strip()}")
            except (PermissionError, IsADirectoryError):
                continue

        return "\n".join(results) if results else "No matches found"
    except Exception as e:
        return f"Error searching code: {str(e)}"


@tool(args_schema=CodeAnalysisInput)
def analyze_code_structure(path: str) -> str:
    """Analyze the structure of a Python file (classes, functions, etc).

    Args:
        path: Python file path to analyze

    Returns:
        Structured analysis of the code
    """
    try:
        file_path = Path(path)
        if not file_path.exists():
            return f"Error: File not found: {path}"

        if not file_path.suffix == ".py":
            return "Error: Only Python files are currently supported"

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        structure = {
            "classes": [],
            "functions": [],
            "imports": [],
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                structure["classes"].append({
                    "name": node.name,
                    "methods": methods,
                    "line": node.lineno,
                })
            elif isinstance(node, ast.FunctionDef):
                structure["functions"].append({
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "line": node.lineno,
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        structure["imports"].append(alias.name)
                else:
                    structure["imports"].append(f"from {node.module}")

        import json
        return json.dumps(structure, indent=2)
    except Exception as e:
        return f"Error analyzing code: {str(e)}"


# Git tool schemas
class GitStatusInput(BaseModel):
    """Input for git status command."""
    path: str = Field(default=".", description="Repository path")


class GitDiffInput(BaseModel):
    """Input for git diff command."""
    path: str = Field(default=".", description="Repository path")
    file: str = Field(default=None, description="Optional specific file to diff")
    staged: bool = Field(default=False, description="Show staged changes only")


class GitLogInput(BaseModel):
    """Input for git log command."""
    path: str = Field(default=".", description="Repository path")
    limit: int = Field(default=10, description="Number of commits to show")
    oneline: bool = Field(default=True, description="Use single-line format")


class BashInput(BaseModel):
    """Input for bash command execution."""
    command: str = Field(description="The bash command to execute")
    working_dir: str = Field(default=".", description="Working directory for command")
    timeout: int = Field(default=30, description="Timeout in seconds")


class FileDiffInput(BaseModel):
    """Input for comparing two files."""
    file1: str = Field(description="Path to first file")
    file2: str = Field(description="Path to second file")
    context_lines: int = Field(default=3, description="Number of context lines around changes")


@tool(args_schema=GitStatusInput)
def git_status(path: str = ".") -> str:
    """Get the current git status of a repository.

    Args:
        path: Path to the git repository

    Returns:
        Git status output
    """
    import subprocess

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "-b"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return f"Error: {result.stderr}"

        output = result.stdout.strip()
        if not output:
            return "Working directory is clean"

        # Parse and format the output
        lines = output.split("\n")
        branch_line = lines[0] if lines else ""
        changes = lines[1:] if len(lines) > 1 else []

        formatted = [f"Branch: {branch_line.replace('## ', '')}"]
        if changes:
            formatted.append("\nChanges:")
            for change in changes:
                status = change[:2]
                filename = change[3:]
                status_map = {
                    "M ": "Modified (staged)",
                    " M": "Modified (unstaged)",
                    "MM": "Modified (staged + unstaged)",
                    "A ": "Added",
                    "D ": "Deleted",
                    " D": "Deleted (unstaged)",
                    "R ": "Renamed",
                    "??": "Untracked",
                }
                status_desc = status_map.get(status, status)
                formatted.append(f"  {status_desc}: {filename}")

        return "\n".join(formatted)
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except FileNotFoundError:
        return "Error: git is not installed or not in PATH"
    except Exception as e:
        return f"Error: {str(e)}"


@tool(args_schema=GitDiffInput)
def git_diff(path: str = ".", file: str = None, staged: bool = False) -> str:
    """Show git diff for changes in the repository.

    Args:
        path: Path to the git repository
        file: Optional specific file to diff
        staged: Whether to show only staged changes

    Returns:
        Git diff output
    """
    import subprocess

    try:
        cmd = ["git", "diff"]
        if staged:
            cmd.append("--staged")
        if file:
            cmd.append("--")
            cmd.append(file)

        result = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return f"Error: {result.stderr}"

        output = result.stdout.strip()
        return output if output else "No changes"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except FileNotFoundError:
        return "Error: git is not installed or not in PATH"
    except Exception as e:
        return f"Error: {str(e)}"


@tool(args_schema=GitLogInput)
def git_log(path: str = ".", limit: int = 10, oneline: bool = True) -> str:
    """Show git commit history.

    Args:
        path: Path to the git repository
        limit: Maximum number of commits to show
        oneline: Use single-line format

    Returns:
        Git log output
    """
    import subprocess

    try:
        cmd = ["git", "log", f"-{limit}"]
        if oneline:
            cmd.append("--oneline")
        else:
            cmd.extend(["--format=%h %s (%an, %ar)"])

        result = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return f"Error: {result.stderr}"

        return result.stdout.strip() or "No commits found"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except FileNotFoundError:
        return "Error: git is not installed or not in PATH"
    except Exception as e:
        return f"Error: {str(e)}"


@tool(args_schema=BashInput)
def run_bash(command: str, working_dir: str = ".", timeout: int = 30) -> str:
    """Execute a bash command safely.

    Args:
        command: The command to execute
        working_dir: Working directory for the command
        timeout: Maximum execution time in seconds

    Returns:
        Command output (stdout and stderr combined)
    """
    import subprocess
    import shlex

    # Safety: Block potentially dangerous commands
    dangerous_patterns = [
        "rm -rf /", "rm -rf ~", "mkfs", "dd if=",
        ":(){", "fork bomb", ">(", "chmod -R 777 /",
        "mv /* ", "mv / ", "curl | sh", "wget | sh",
    ]

    command_lower = command.lower()
    for pattern in dangerous_patterns:
        if pattern in command_lower:
            return f"Error: Potentially dangerous command blocked: {pattern}"

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        output = []
        if result.stdout:
            output.append(result.stdout)
        if result.stderr:
            output.append(f"[stderr]\n{result.stderr}")
        if result.returncode != 0:
            output.append(f"\n[exit code: {result.returncode}]")

        return "\n".join(output).strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"


@tool(args_schema=FileDiffInput)
def file_diff(file1: str, file2: str, context_lines: int = 3) -> str:
    """Compare two files and show differences.

    Args:
        file1: Path to first file
        file2: Path to second file
        context_lines: Number of context lines around changes

    Returns:
        Unified diff output
    """
    import difflib

    try:
        path1 = Path(file1)
        path2 = Path(file2)

        if not path1.exists():
            return f"Error: File not found: {file1}"
        if not path2.exists():
            return f"Error: File not found: {file2}"

        with open(path1, "r", encoding="utf-8") as f:
            lines1 = f.readlines()
        with open(path2, "r", encoding="utf-8") as f:
            lines2 = f.readlines()

        diff = difflib.unified_diff(
            lines1,
            lines2,
            fromfile=str(path1),
            tofile=str(path2),
            n=context_lines
        )

        result = "".join(diff)
        return result if result else "Files are identical"
    except Exception as e:
        return f"Error comparing files: {str(e)}"


# Git tools list
GIT_TOOLS = [
    git_status,
    git_diff,
    git_log,
]

# Utility tools list
UTIL_TOOLS = [
    run_bash,
    file_diff,
]

# Create a list of all tools for easy registration
CODE_TOOLS = [
    read_file,
    write_file,
    edit_file,
    list_directory,
    search_code,
    analyze_code_structure,
]

# All tools combined
ALL_TOOLS = CODE_TOOLS + GIT_TOOLS + UTIL_TOOLS
