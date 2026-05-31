"""
Session Memory — Chapter 5: Memory Systems and Context Management

Short-term, task-scoped memory. Stores key-value pairs for the duration
of one agent session. Automatically expires on session end.
"""
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionMemory:
    """In-memory key-value store scoped to a single agent task."""
    session_id: str
    _store: dict = field(default_factory=dict, repr=False)
    _created: float = field(default_factory=time.time, repr=False)

    def write(self, key: str, value: Any) -> None:
        self._store[key] = {"value": value, "timestamp": time.time()}

    def read(self, key: str) -> Any:
        entry = self._store.get(key)
        return entry["value"] if entry else None

    def read_all(self) -> dict:
        return {k: v["value"] for k, v in self._store.items()}

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def age_seconds(self) -> float:
        return time.time() - self._created

    def snapshot(self) -> str:
        """Serializable text snapshot for context injection."""
        if not self._store:
            return "(empty)"
        lines = []
        for k, v in self._store.items():
            age = int(time.time() - v["timestamp"])
            lines.append(f"{k}: {v['value']} (stored {age}s ago)")
        return "\n".join(lines)
