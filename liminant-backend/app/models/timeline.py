from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
import uuid


class TimelineEvent(BaseModel):
    id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:10]}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str
    description: str
    metadata: dict = Field(default_factory=dict)

    def to_dict(self) -> dict:
        d = self.model_dump(mode="json")
        d["timestamp"] = self.timestamp.isoformat()
        return d


class SessionTimeline:
    def __init__(self, session_id: str, events: list[dict] | None = None):
        self.session_id = session_id
        self.events: list[dict] = events or []

    def add(self, event_type: str, description: str, metadata: dict | None = None) -> dict:
        event = TimelineEvent(
            event_type=event_type,
            description=description,
            metadata=metadata or {},
        )
        self.events.append(event.to_dict())
        return event.to_dict()

    def add_message(self, role: str, content_preview: str) -> dict:
        return self.add(
            "message",
            f"{role}: {content_preview[:80]}",
            {"role": role, "preview_length": len(content_preview)},
        )

    def add_artifact(self, path: str, artifact_type: str, summary: str) -> dict:
        return self.add(
            "artifact",
            f"Created: {path}",
            {"path": path, "artifact_type": artifact_type, "summary": summary},
        )

    def add_constraint_change(self, action: str, ref_id: str) -> dict:
        return self.add(
            "constraint_change",
            f"Constraint {action}: {ref_id}",
            {"action": action, "ref_id": ref_id},
        )

    def add_phase_change(self, from_phase: str, to_phase: str) -> dict:
        return self.add(
            "phase_change",
            f"Phase: {from_phase} → {to_phase}",
            {"from": from_phase, "to": to_phase},
        )

    def get_events(self, event_type: str | None = None) -> list[dict]:
        if event_type:
            return [e for e in self.events if e["event_type"] == event_type]
        return self.events

    def get_grouped_by_date(self) -> dict[str, list[dict]]:
        grouped: dict[str, list[dict]] = {}
        for event in self.events:
            date = event["timestamp"][:10]
            if date not in grouped:
                grouped[date] = []
            grouped[date].append(event)
        return grouped

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "events": self.events,
            "total_events": len(self.events),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionTimeline":
        return cls(session_id=data["session_id"], events=data.get("events", []))
