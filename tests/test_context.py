"""Tests for context and memory management."""

import pytest
import tempfile
import json
from pathlib import Path
from langcode.context import ConversationContext, ContextManager


def test_conversation_context_initialization():
    """Test ConversationContext initialization."""
    context = ConversationContext(session_id="test-session")

    assert context.session_id == "test-session"
    assert context.messages == []
    assert context.file_buffer == {}
    assert context.metadata == {}


def test_add_message():
    """Test adding messages to context."""
    context = ConversationContext(session_id="test")

    context.add_message("user", "Hello")
    context.add_message("assistant", "Hi there")

    assert len(context.messages) == 2
    assert context.messages[0]["role"] == "user"
    assert context.messages[1]["role"] == "assistant"


def test_get_message_history():
    """Test retrieving message history."""
    context = ConversationContext(session_id="test")

    for i in range(5):
        context.add_message("user", f"Message {i}")

    history = context.get_message_history()
    assert len(history) == 5

    # Test limiting history
    limited = context.get_message_history(limit=3)
    assert len(limited) == 3


def test_cache_file():
    """Test caching files."""
    context = ConversationContext(session_id="test")

    context.cache_file("file1.py", "content1")
    context.cache_file("file2.py", "content2")

    assert context.get_cached_file("file1.py") == "content1"
    assert context.get_cached_file("file2.py") == "content2"


def test_clear_cache():
    """Test clearing file cache."""
    context = ConversationContext(session_id="test")

    context.cache_file("file1.py", "content")
    assert len(context.file_buffer) == 1

    context.clear_cache()
    assert len(context.file_buffer) == 0


def test_metadata_operations():
    """Test metadata operations."""
    context = ConversationContext(session_id="test")

    context.set_metadata("current_file", "agent.py")
    context.set_metadata("language", "python")

    assert context.get_metadata("current_file") == "agent.py"
    assert context.get_metadata("language") == "python"
    assert context.get_metadata("nonexistent", "default") == "default"


def test_context_serialization():
    """Test converting context to dictionary."""
    context = ConversationContext(session_id="test")
    context.add_message("user", "Hello")
    context.set_metadata("key", "value")

    data = context.to_dict()

    assert data["session_id"] == "test"
    assert len(data["messages"]) == 1
    assert data["metadata"]["key"] == "value"


def test_save_and_load_context():
    """Test saving and loading context from file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        context = ConversationContext(session_id="test-session")
        context.add_message("user", "Hello")
        context.add_message("assistant", "Hi")
        context.set_metadata("working_dir", "/tmp")

        filepath = Path(tmpdir) / "context.json"

        # Save
        context.save(str(filepath))
        assert filepath.exists()

        # Load
        loaded = ConversationContext.load(str(filepath))

        assert loaded.session_id == "test-session"
        assert len(loaded.messages) == 2
        assert loaded.get_metadata("working_dir") == "/tmp"


def test_context_manager_initialization():
    """Test ContextManager initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ContextManager(storage_dir=tmpdir)

        assert manager.storage_dir.exists()
        assert manager.current_context is None


def test_create_context():
    """Test creating a new context."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ContextManager(storage_dir=tmpdir)
        context = manager.create_context("session1", working_directory="/tmp")

        assert context.session_id == "session1"
        assert manager.current_context == context


def test_save_and_load_context_via_manager():
    """Test saving and loading contexts via manager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ContextManager(storage_dir=tmpdir)

        # Create and save
        context = manager.create_context("session1")
        context.add_message("user", "test")
        manager.save_current_context()

        # Load
        loaded = manager.load_context("session1")

        assert loaded is not None
        assert loaded.session_id == "session1"
        assert len(loaded.messages) == 1


def test_list_contexts():
    """Test listing saved contexts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ContextManager(storage_dir=tmpdir)

        # Create multiple contexts
        manager.create_context("session1")
        manager.save_current_context()

        manager.create_context("session2")
        manager.save_current_context()

        contexts = manager.list_contexts()

        assert "session1" in contexts
        assert "session2" in contexts
        assert len(contexts) == 2


def test_nonexistent_context():
    """Test loading nonexistent context."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ContextManager(storage_dir=tmpdir)

        loaded = manager.load_context("nonexistent")
        assert loaded is None
