"""Tests for new tools (git, bash, file_diff)."""

import pytest
import tempfile
import os
from pathlib import Path
from langcode.tools import (
    git_status,
    git_diff,
    git_log,
    run_bash,
    file_diff,
    GIT_TOOLS,
    UTIL_TOOLS,
    ALL_TOOLS,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def git_repo(temp_dir):
    """Create a temporary git repository."""
    import subprocess

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=temp_dir,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=temp_dir,
        capture_output=True,
    )

    # Create initial commit
    Path(temp_dir).joinpath("README.md").write_text("# Test\n")
    subprocess.run(["git", "add", "README.md"], cwd=temp_dir, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=temp_dir,
        capture_output=True,
    )

    yield temp_dir


class TestGitStatus:
    """Tests for git_status tool."""

    def test_clean_repo(self, git_repo):
        """Test status on clean repo."""
        result = git_status.invoke({"path": git_repo})
        assert "Branch:" in result or "clean" in result.lower()

    def test_modified_file(self, git_repo):
        """Test status with modified file."""
        # Modify a file
        Path(git_repo).joinpath("README.md").write_text("# Test Modified\n")

        result = git_status.invoke({"path": git_repo})
        assert "Modified" in result or "README.md" in result

    def test_untracked_file(self, git_repo):
        """Test status with untracked file."""
        Path(git_repo).joinpath("new_file.txt").write_text("new content")

        result = git_status.invoke({"path": git_repo})
        assert "Untracked" in result or "new_file.txt" in result

    def test_not_a_repo(self, temp_dir):
        """Test status on non-git directory."""
        result = git_status.invoke({"path": temp_dir})
        assert "Error" in result or "not a git repository" in result.lower()


class TestGitDiff:
    """Tests for git_diff tool."""

    def test_no_changes(self, git_repo):
        """Test diff with no changes."""
        result = git_diff.invoke({"path": git_repo})
        assert "No changes" in result or result.strip() == ""

    def test_unstaged_changes(self, git_repo):
        """Test diff with unstaged changes."""
        Path(git_repo).joinpath("README.md").write_text("# Modified Content\n")

        result = git_diff.invoke({"path": git_repo})
        assert "Modified Content" in result or "diff" in result.lower()

    def test_staged_changes(self, git_repo):
        """Test diff with staged changes."""
        import subprocess

        Path(git_repo).joinpath("README.md").write_text("# Staged Content\n")
        subprocess.run(["git", "add", "README.md"], cwd=git_repo, capture_output=True)

        result = git_diff.invoke({"path": git_repo, "staged": True})
        assert "Staged Content" in result or "diff" in result.lower()


class TestGitLog:
    """Tests for git_log tool."""

    def test_show_commits(self, git_repo):
        """Test showing commit history."""
        result = git_log.invoke({"path": git_repo, "limit": 5})
        assert "Initial commit" in result

    def test_limit_commits(self, git_repo):
        """Test limiting number of commits."""
        import subprocess

        # Add more commits
        for i in range(3):
            Path(git_repo).joinpath(f"file{i}.txt").write_text(f"content {i}")
            subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", f"Commit {i}"],
                cwd=git_repo,
                capture_output=True,
            )

        result = git_log.invoke({"path": git_repo, "limit": 2})
        lines = [l for l in result.strip().split("\n") if l]
        assert len(lines) <= 2


class TestRunBash:
    """Tests for run_bash tool."""

    def test_simple_command(self, temp_dir):
        """Test simple command execution."""
        result = run_bash.invoke({"command": "echo hello", "working_dir": temp_dir})
        assert "hello" in result

    def test_command_with_output(self, temp_dir):
        """Test command with file output."""
        Path(temp_dir).joinpath("test.txt").write_text("file content")

        result = run_bash.invoke({"command": "cat test.txt", "working_dir": temp_dir})
        assert "file content" in result

    def test_command_error(self, temp_dir):
        """Test command that fails."""
        result = run_bash.invoke(
            {"command": "ls nonexistent_dir_12345", "working_dir": temp_dir}
        )
        assert "exit code" in result.lower() or "stderr" in result.lower() or "No such" in result

    def test_dangerous_command_blocked(self, temp_dir):
        """Test that dangerous commands are blocked."""
        result = run_bash.invoke({"command": "rm -rf /", "working_dir": temp_dir})
        assert "Error" in result or "blocked" in result.lower()

    def test_timeout(self, temp_dir):
        """Test command timeout."""
        result = run_bash.invoke(
            {"command": "sleep 5", "working_dir": temp_dir, "timeout": 1}
        )
        assert "timed out" in result.lower()


class TestFileDiff:
    """Tests for file_diff tool."""

    def test_identical_files(self, temp_dir):
        """Test diff of identical files."""
        file1 = Path(temp_dir) / "file1.txt"
        file2 = Path(temp_dir) / "file2.txt"
        file1.write_text("same content\n")
        file2.write_text("same content\n")

        result = file_diff.invoke({"file1": str(file1), "file2": str(file2)})
        assert "identical" in result.lower()

    def test_different_files(self, temp_dir):
        """Test diff of different files."""
        file1 = Path(temp_dir) / "file1.txt"
        file2 = Path(temp_dir) / "file2.txt"
        file1.write_text("line 1\nline 2\nline 3\n")
        file2.write_text("line 1\nmodified line\nline 3\n")

        result = file_diff.invoke({"file1": str(file1), "file2": str(file2)})
        assert "---" in result or "+++" in result
        assert "modified" in result

    def test_missing_file(self, temp_dir):
        """Test diff with missing file."""
        file1 = Path(temp_dir) / "existing.txt"
        file1.write_text("content")

        result = file_diff.invoke(
            {"file1": str(file1), "file2": "/nonexistent/file.txt"}
        )
        assert "Error" in result or "not found" in result.lower()


class TestToolLists:
    """Tests for tool list exports."""

    def test_git_tools_list(self):
        """Test GIT_TOOLS list."""
        assert len(GIT_TOOLS) == 3
        tool_names = [t.name for t in GIT_TOOLS]
        assert "git_status" in tool_names
        assert "git_diff" in tool_names
        assert "git_log" in tool_names

    def test_util_tools_list(self):
        """Test UTIL_TOOLS list."""
        assert len(UTIL_TOOLS) == 2
        tool_names = [t.name for t in UTIL_TOOLS]
        assert "run_bash" in tool_names
        assert "file_diff" in tool_names

    def test_all_tools_list(self):
        """Test ALL_TOOLS list."""
        # Should include CODE_TOOLS + GIT_TOOLS + UTIL_TOOLS
        assert len(ALL_TOOLS) >= 11
        tool_names = [t.name for t in ALL_TOOLS]

        # CODE_TOOLS
        assert "read_file" in tool_names
        assert "write_file" in tool_names

        # GIT_TOOLS
        assert "git_status" in tool_names

        # UTIL_TOOLS
        assert "run_bash" in tool_names
