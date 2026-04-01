from typing import Any
from app.models.knowledge import KnowledgeEntry, KnowledgeCreate, KnowledgeType
from app.models.session import Session
from app.utils.json_storage import get_storage
from datetime import datetime


class KnowledgeBase:
    def __init__(self):
        self.storage = get_storage()

    async def create(self, data: KnowledgeCreate) -> KnowledgeEntry:
        entry = KnowledgeEntry(
            type=data.type,
            content={"title": data.title, "body": data.body, "examples": []},
            metadata={"tags": data.tags, "source": "user_defined", "confidence": 0.95, "usage_count": 0},
            triggers={"keywords": data.keywords, "session_types": [], "context_patterns": []},
        )
        await self.storage.write("knowledge", entry.id, entry.to_dict())
        return entry

    async def get(self, kb_id: str) -> KnowledgeEntry | None:
        data = await self.storage.read("knowledge", kb_id)
        if data is None:
            return None
        return KnowledgeEntry(**data)

    async def update(self, kb_id: str, data: dict) -> KnowledgeEntry | None:
        entry = await self.get(kb_id)
        if entry is None:
            return None
        for key, value in data.items():
            if key == "metadata":
                for mk, mv in value.items():
                    if hasattr(entry.metadata, mk):
                        setattr(entry.metadata, mk, mv)
            elif hasattr(entry, key):
                setattr(entry, key, value)
        entry.updated_at = datetime.utcnow()
        await self.storage.write("knowledge", entry.id, entry.to_dict())
        return entry

    async def delete(self, kb_id: str) -> bool:
        return await self.storage.delete("knowledge", kb_id)

    async def list_entries(self) -> list[KnowledgeEntry]:
        keys = await self.storage.list_keys("knowledge")
        entries = []
        for key in keys:
            data = await self.storage.read("knowledge", key)
            if data:
                entries.append(KnowledgeEntry(**data))
        return entries

    async def search(
        self, query: str, limit: int = 10, session_type: str | None = None
    ) -> list[KnowledgeEntry]:
        all_entries = await self.list_entries()
        query_lower = query.lower()
        scored = []
        for entry in all_entries:
            score = self._score_entry(entry, query_lower, session_type)
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: (x[0], x[1].metadata.usage_count), reverse=True)
        return [entry for _, entry in scored[:limit]]

    def _score_entry(self, entry: KnowledgeEntry, query_lower: str, session_type: str | None) -> float:
        score = 0.0

        if query_lower in entry.content.title.lower():
            score += 3.0
        if query_lower in entry.content.body.lower():
            score += 2.0
        if any(query_lower in kw.lower() for kw in entry.triggers.keywords):
            score += 1.5

        if entry.type == KnowledgeType.RULE:
            score *= 1.2
        elif entry.type == KnowledgeType.PATTERN:
            score *= 1.1

        if session_type and session_type in entry.triggers.session_types:
            score *= 1.3

        recency_days = (datetime.utcnow() - entry.updated_at).days
        if recency_days < 7:
            score *= 1.1
        elif recency_days > 90:
            score *= 0.9

        return score

    async def trigger_for_session(self, session: dict[str, Any]) -> list[KnowledgeEntry]:
        working_dir = session.get("context", {}).get("working_directory", "")
        phase = session.get("state", {}).get("phase", "")
        all_entries = await self.list_entries()

        triggered = []
        for entry in all_entries:
            if self._matches_context(entry, working_dir, phase):
                triggered.append(entry)

        triggered.sort(key=lambda e: e.metadata.confidence, reverse=True)
        return triggered[:5]

    def _matches_context(self, entry: KnowledgeEntry, working_dir: str, phase: str) -> bool:
        for pattern in entry.triggers.context_patterns:
            if pattern in working_dir.lower():
                return True
        if phase and phase in entry.triggers.session_types:
            return True
        if not entry.triggers.context_patterns and not entry.triggers.session_types:
            return entry.type == KnowledgeType.RULE
        return False

    async def increment_usage(self, kb_id: str) -> None:
        entry = await self.get(kb_id)
        if entry:
            entry.metadata.usage_count += 1
            entry.metadata.confidence = min(0.99, entry.metadata.confidence + 0.005)
            await self.storage.write("knowledge", entry.id, entry.to_dict())

    async def record_outcome(self, kb_id: str, positive: bool) -> None:
        entry = await self.get(kb_id)
        if not entry:
            return
        entry.metadata.usage_count += 1
        delta = 0.02 if positive else -0.01
        entry.metadata.confidence = max(0.1, min(0.99, entry.metadata.confidence + delta))
        entry.metadata.usage_count += 1
        await self.storage.write("knowledge", entry.id, entry.to_dict())

    async def get_statistics(self) -> dict[str, Any]:
        entries = await self.list_entries()
        total = len(entries)
        by_type = {}
        for e in entries:
            t = e.type.value
            by_type[t] = by_type.get(t, 0) + 1
        total_usage = sum(e.metadata.usage_count for e in entries)
        avg_confidence = sum(e.metadata.confidence for e in entries) / total if total else 0
        return {
            "total_entries": total,
            "by_type": by_type,
            "total_usage": total_usage,
            "average_confidence": round(avg_confidence, 3),
        }
