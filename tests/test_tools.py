"""Tests for code manipulation tools."""

import pytest
import tempfile
from pathlib import Path
from langcode.tools import (
    read_file,
    write_file,
    edit_file,
    list_directory,
    search_code,
    analyze_code_structure,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_write_and_read_file(temp_dir):
    """Test writing and reading a file."""
    filepath = Path(temp_dir) / "test.txt"
    content = "Hello, World!"

    # Write file
    result = write_file.invoke({"path": str(filepath), "content": content})
    assert "Successfully wrote" in result

    # Read file
    read_content = read_file.invoke({"path": str(filepath)})
    assert read_content == content


def test_edit_file(temp_dir):
    """Test editing a file."""
    filepath = Path(temp_dir) / "test.py"
    original = "def hello():\n    print('hello')"
    updated = "def hello():\n    print('world')"

    write_file.invoke({"path": str(filepath), "content": original})

    # Edit file
    result = edit_file.invoke({
        "path": str(filepath),
        "old_content": "print('hello')",
        "new_content": "print('world')"
    })
    assert "Successfully edited" in result

    # Verify changes
    content = read_file.invoke({"path": str(filepath)})
    assert content == updated


def test_read_file_with_line_range(temp_dir):
    """Test reading a file with line range."""
    filepath = Path(temp_dir) / "test.txt"
    content = "line 1\nline 2\nline 3\nline 4"

    write_file.invoke({"path": str(filepath), "content": content})

    # Read lines 2-3
    result = read_file.invoke({"path": str(filepath), "start_line": 2, "end_line": 3})
    assert "line 2" in result
    assert "line 3" in result
    assert "line 1" not in result


def test_list_directory(temp_dir):
    """Test listing directory contents."""
    # Create some files
    Path(temp_dir).joinpath("file1.txt").write_text("content1")
    Path(temp_dir).joinpath("file2.py").write_text("content2")
    Path(temp_dir).joinpath("subdir").mkdir()

    result = list_directory.invoke({"path": temp_dir})
    assert "file1.txt" in result
    assert "file2.py" in result
    assert "subdir" in result


def test_search_code(temp_dir):
    """Test code pattern search."""
    # Create Python files
    Path(temp_dir).joinpath("test.py").write_text("def hello():\n    pass\n")
    Path(temp_dir).joinpath("other.py").write_text("def world():\n    pass\n")

    result = search_code.invoke({"pattern": r"def \w+\(\):", "path": temp_dir, "file_type": "py"})
    assert "def hello" in result
    assert "def world" in result


def test_analyze_code_structure(temp_dir):
    """Test code structure analysis."""
    # Create a Python file
    code = """
class MyClass:
    def method1(self):
        pass

    def method2(self, arg):
        pass

def my_function(x, y):
    pass
"""
    filepath = Path(temp_dir) / "test.py"
    write_file.invoke({"path": str(filepath), "content": code})

    result = analyze_code_structure.invoke({"path": str(filepath)})
    assert "MyClass" in result
    assert "method1" in result
    assert "method2" in result
    assert "my_function" in result


def test_file_not_found():
    """Test handling of missing files."""
    result = read_file.invoke({"path": "/nonexistent/file.txt"})
    assert "Error" in result or "not found" in result.lower()


def test_edit_nonexistent_content(temp_dir):
    """Test editing with content that doesn't exist."""
    filepath = Path(temp_dir) / "test.txt"
    write_file.invoke({"path": str(filepath), "content": "hello world"})

    result = edit_file.invoke({
        "path": str(filepath),
        "old_content": "nonexistent",
        "new_content": "replacement"
    })
    assert "Error" in result or "not found" in result.lower()
