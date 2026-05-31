"""
Validated Memory Store — Chapter 9: System Reliability and Safety

Write-time confidence gate: low-confidence values are not persisted.
Read-time staleness warning: entries older than 24 hours get a warning flag.

Rule: never write unvalidated agent output directly to memory.
Every stored value carries confidence + source for audit and retrieval filtering.
"""
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryEntry:
    value: Any
    source: str
    confidence: float
    stored_at: float = field(default_factory=time.time)


class ValidatedMemoryStore:
    CONFIDENCE_THRESHOLD = 0.7
    STALENESS_HOURS      = 24.0

    def __init__(self):
        self._store: dict[str, MemoryEntry] = {}

    def write(self, key: str, value: Any, source: str = "agent", confidence: float = 1.0) -> dict:
        if confidence < self.CONFIDENCE_THRESHOLD:
            return {
                "written": False,
                "reason": f"Confidence {confidence:.2f} below threshold {self.CONFIDENCE_THRESHOLD}.",
            }
        self._store[key] = MemoryEntry(value=value, source=source, confidence=confidence)
        return {"written": True}

    def read(self, key: str) -> dict:
        entry = self._store.get(key)
        if entry is None:
            return {"found": False, "value": None, "confidence": 0.0, "age_hours": 0.0}

        age_hours = (time.time() - entry.stored_at) / 3600
        warning = "Stale — verify before using" if age_hours > self.STALENESS_HOURS else None

        return {
            "found":      True,
            "value":      entry.value,
            "source":     entry.source,
            "confidence": entry.confidence,
            "age_hours":  round(age_hours, 2),
            "warning":    warning,
        }

    def delete(self, key: str) -> None:
        self._store.pop(key, None)
