"""Advanced code analysis for symbol finding, type hints, and semantic understanding."""

import ast
from typing import Optional, list, dict, Any
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Symbol:
    """Represents a code symbol (class, function, variable, etc)."""

    name: str
    type: str  # "class", "function", "variable", "method"
    file_path: str
    line_start: int
    line_end: int
    parent: Optional[str] = None  # For methods, the parent class
    docstring: Optional[str] = None
    arguments: list[str] = None
    return_type: Optional[str] = None

    def __post_init__(self):
        if self.arguments is None:
            self.arguments = []


class CodeAnalyzer:
    """Advanced code analyzer for Python files."""

    def __init__(self):
        """Initialize the analyzer."""
        self.symbols: dict[str, list[Symbol]] = {}
        self.trees: dict[str, ast.AST] = {}

    def analyze_file(self, filepath: str) -> list[Symbol]:
        """Analyze a Python file and extract symbols."""
        path = Path(filepath)

        if not path.exists():
            return []

        if not path.suffix == ".py":
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            self.trees[filepath] = tree

            symbols = []
            self._extract_symbols(tree, filepath, symbols)

            self.symbols[filepath] = symbols
            return symbols
        except Exception:
            return []

    def _extract_symbols(self, tree: ast.AST, filepath: str, symbols: list[Symbol], parent: Optional[str] = None):
        """Recursively extract symbols from AST."""
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                symbol = Symbol(
                    name=node.name,
                    type="class",
                    file_path=filepath,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    docstring=ast.get_docstring(node),
                )
                symbols.append(symbol)

                # Extract methods from class
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_symbol = Symbol(
                            name=item.name,
                            type="method",
                            file_path=filepath,
                            line_start=item.lineno,
                            line_end=item.end_lineno or item.lineno,
                            parent=node.name,
                            docstring=ast.get_docstring(item),
                            arguments=[arg.arg for arg in item.args.args if arg.arg != "self"],
                            return_type=self._extract_return_type(item),
                        )
                        symbols.append(method_symbol)

            elif isinstance(node, ast.FunctionDef):
                symbol = Symbol(
                    name=node.name,
                    type="function",
                    file_path=filepath,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    docstring=ast.get_docstring(node),
                    arguments=[arg.arg for arg in node.args.args],
                    return_type=self._extract_return_type(node),
                )
                symbols.append(symbol)

    def _extract_return_type(self, node: ast.FunctionDef) -> Optional[str]:
        """Extract return type from function annotation."""
        if node.returns:
            return ast.unparse(node.returns)
        return None

    def find_symbol(self, name: str, file_path: Optional[str] = None) -> list[Symbol]:
        """Find symbols by name."""
        results = []

        if file_path:
            if file_path not in self.symbols:
                self.analyze_file(file_path)

            if file_path in self.symbols:
                results = [s for s in self.symbols[file_path] if s.name == name]
        else:
            for symbols in self.symbols.values():
                results.extend([s for s in symbols if s.name == name])

        return results

    def find_references(self, symbol_name: str, file_path: Optional[str] = None) -> list[tuple[str, int, str]]:
        """Find references to a symbol.

        Returns: List of (filepath, line_number, context) tuples
        """
        results = []
        files_to_search = [file_path] if file_path else list(self.trees.keys())

        for filepath in files_to_search:
            if filepath not in self.trees:
                self.analyze_file(filepath)

            if filepath in self.trees:
                tree = self.trees[filepath]
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Name) and node.id == symbol_name:
                            line_num = node.lineno
                            context = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                            results.append((filepath, line_num, context))
                except Exception:
                    continue

        return results

    def get_symbol_info(self, name: str, filepath: Optional[str] = None) -> Optional[dict[str, Any]]:
        """Get detailed information about a symbol."""
        symbols = self.find_symbol(name, filepath)

        if not symbols:
            return None

        symbol = symbols[0]

        return {
            "name": symbol.name,
            "type": symbol.type,
            "file": symbol.file_path,
            "line_start": symbol.line_start,
            "line_end": symbol.line_end,
            "parent": symbol.parent,
            "docstring": symbol.docstring,
            "arguments": symbol.arguments,
            "return_type": symbol.return_type,
        }

    def analyze_directory(self, directory: str) -> dict[str, list[Symbol]]:
        """Analyze all Python files in a directory."""
        path = Path(directory)

        for py_file in path.rglob("*.py"):
            if ".venv" not in py_file.parts and "__pycache__" not in py_file.parts:
                self.analyze_file(str(py_file))

        return self.symbols


# Create tool functions for the analyzer
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class FindSymbolInput(BaseModel):
    """Input for finding a symbol."""
    name: str = Field(description="The symbol name to find")
    file_path: str = Field(default=None, description="Optional file path to search in")


class FindReferencesInput(BaseModel):
    """Input for finding references to a symbol."""
    name: str = Field(description="The symbol name to find references for")
    file_path: str = Field(default=None, description="Optional file path to search in")


# Global analyzer instance
_analyzer = CodeAnalyzer()


@tool(args_schema=FindSymbolInput)
def find_symbol(name: str, file_path: str = None) -> str:
    """Find a symbol (class, function, method) in the codebase.

    Args:
        name: Symbol name to find
        file_path: Optional file to search in

    Returns:
        Information about found symbols
    """
    import json

    symbols = _analyzer.find_symbol(name, file_path)

    if not symbols:
        return f"No symbol found with name: {name}"

    result = []
    for symbol in symbols:
        result.append({
            "name": symbol.name,
            "type": symbol.type,
            "file": symbol.file_path,
            "line": symbol.line_start,
            "docstring": symbol.docstring,
        })

    return json.dumps(result, indent=2)


@tool(args_schema=FindReferencesInput)
def find_references(name: str, file_path: str = None) -> str:
    """Find all references to a symbol in the codebase.

    Args:
        name: Symbol name to find references for
        file_path: Optional file to search in

    Returns:
        List of references with context
    """
    references = _analyzer.find_references(name, file_path)

    if not references:
        return f"No references found for: {name}"

    result = [f"{file}:{line} - {context}" for file, line, context in references]
    return "\n".join(result)


ANALYZER_TOOLS = [find_symbol, find_references]
