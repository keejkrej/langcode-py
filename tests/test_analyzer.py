"""Tests for the code analyzer."""

import pytest
import tempfile
from pathlib import Path
from langcode.analyzer import CodeAnalyzer, Symbol


@pytest.fixture
def analyzer():
    """Create a CodeAnalyzer instance."""
    return CodeAnalyzer()


@pytest.fixture
def python_file(example_python_code):
    """Create a temporary Python file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(example_python_code)
        f.flush()
        yield f.name

    # Cleanup
    Path(f.name).unlink()


def test_analyzer_initialization(analyzer):
    """Test analyzer initialization."""
    assert analyzer.symbols == {}
    assert analyzer.trees == {}


def test_analyze_file(analyzer, python_file):
    """Test analyzing a Python file."""
    symbols = analyzer.analyze_file(python_file)

    assert len(symbols) > 0
    assert python_file in analyzer.symbols
    assert python_file in analyzer.trees


def test_find_class_symbol(analyzer, python_file):
    """Test finding a class symbol."""
    analyzer.analyze_file(python_file)
    symbols = analyzer.find_symbol("Calculator", python_file)

    assert len(symbols) == 1
    assert symbols[0].name == "Calculator"
    assert symbols[0].type == "class"
    assert "simple calculator" in symbols[0].docstring.lower()


def test_find_method_symbol(analyzer, python_file):
    """Test finding a method symbol."""
    analyzer.analyze_file(python_file)
    symbols = analyzer.find_symbol("add", python_file)

    assert len(symbols) == 1
    assert symbols[0].name == "add"
    assert symbols[0].type == "method"
    assert symbols[0].parent == "Calculator"


def test_find_function_symbol(analyzer, python_file):
    """Test finding a function symbol."""
    analyzer.analyze_file(python_file)
    symbols = analyzer.find_symbol("main", python_file)

    assert len(symbols) == 1
    assert symbols[0].name == "main"
    assert symbols[0].type == "function"


def test_method_arguments(analyzer, python_file):
    """Test extracting method arguments."""
    analyzer.analyze_file(python_file)
    symbols = analyzer.find_symbol("add", python_file)

    assert "a" in symbols[0].arguments
    assert "b" in symbols[0].arguments


def test_return_type_extraction(analyzer, python_file):
    """Test extracting return types."""
    analyzer.analyze_file(python_file)
    symbols = analyzer.find_symbol("add", python_file)

    assert symbols[0].return_type == "int"


def test_symbol_info(analyzer, python_file):
    """Test getting detailed symbol information."""
    analyzer.analyze_file(python_file)
    info = analyzer.get_symbol_info("Calculator", python_file)

    assert info is not None
    assert info["name"] == "Calculator"
    assert info["type"] == "class"
    assert info["file"] == python_file


def test_nonexistent_file(analyzer):
    """Test handling nonexistent files."""
    symbols = analyzer.analyze_file("/nonexistent/file.py")
    assert symbols == []


def test_non_python_file(analyzer):
    """Test handling non-Python files."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("not python code")
        f.flush()

        symbols = analyzer.analyze_file(f.name)
        assert symbols == []

        Path(f.name).unlink()


def test_analyze_directory(analyzer, example_python_code):
    """Test analyzing a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple files
        Path(tmpdir).joinpath("file1.py").write_text(example_python_code)
        Path(tmpdir).joinpath("file2.py").write_text("def foo():\n    pass\n")

        result = analyzer.analyze_directory(tmpdir)

        assert len(result) == 2
        # Verify symbols were found in both files
        total_symbols = sum(len(symbols) for symbols in result.values())
        assert total_symbols > 0
