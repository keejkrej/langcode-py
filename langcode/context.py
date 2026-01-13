"""Context and memory management for conversation state."""

from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime
from pathlib import Path
import json


@dataclass
class ConversationContext:
    """Manages context and memory for ongoing conversations."""

    session_id: str
    working_directory: str = "."
    created_at: datetime = field(default_factory=datetime.now)
    messages: list[dict[str, str]] = field(default_factory=list)
    file_buffer: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })

    def get_message_history(self, limit: Optional[int] = None) -> list[dict[str, str]]:
        """Get message history, optionally limited to recent messages."""
        if limit:
            return self.messages[-limit:]
        return self.messages

    def cache_file(self, path: str, content: str):
        """Cache file content to avoid repeated reads."""
        self.file_buffer[path] = content

    def get_cached_file(self, path: str) -> Optional[str]:
        """Get cached file content if available."""
        return self.file_buffer.get(path)

    def clear_cache(self):
        """Clear the file buffer cache."""
        self.file_buffer.clear()

    def set_metadata(self, key: str, value: Any):
        """Set metadata about the session."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata about the session."""
        return self.metadata.get(key, default)

    def to_dict(self) -> dict:
        """Convert context to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "working_directory": self.working_directory,
            "created_at": self.created_at.isoformat(),
            "messages": self.messages,
            "metadata": self.metadata,
        }

    def save(self, filepath: str):
        """Save context to a JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "ConversationContext":
        """Load context from a JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        context = cls(
            session_id=data["session_id"],
            working_directory=data.get("working_directory", "."),
            created_at=datetime.fromisoformat(data["created_at"]),
            messages=data.get("messages", []),
            metadata=data.get("metadata", {}),
        )
        return context


class ContextManager:
    """Manages multiple conversation contexts."""

    def __init__(self, storage_dir: str = ".langcode"):
        """Initialize the context manager."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.current_context: Optional[ConversationContext] = None

    def create_context(self, session_id: str, working_directory: str = ".") -> ConversationContext:
        """Create a new conversation context."""
        self.current_context = ConversationContext(
            session_id=session_id,
            working_directory=working_directory,
        )
        return self.current_context

    def load_context(self, session_id: str) -> Optional[ConversationContext]:
        """Load a saved conversation context."""
        filepath = self.storage_dir / f"{session_id}.json"
        if filepath.exists():
            self.current_context = ConversationContext.load(str(filepath))
            return self.current_context
        return None

    def save_current_context(self):
        """Save the current context."""
        if self.current_context:
            filepath = self.storage_dir / f"{self.current_context.session_id}.json"
            self.current_context.save(str(filepath))

    def list_contexts(self) -> list[str]:
        """List all saved contexts."""
        return [f.stem for f in self.storage_dir.glob("*.json")]
