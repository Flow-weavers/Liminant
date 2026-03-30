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
            if hasattr(entry, key):
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
            score = 0
            if query_lower in entry.content.title.lower():
                score += 3
            if query_lower in entry.content.body.lower():
                score += 2
            if any(query_lower in kw.lower() for kw in entry.triggers.keywords):
                score += 1
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:limit]]

    async def increment_usage(self, kb_id: str) -> None:
        entry = await self.get(kb_id)
        if entry:
            entry.metadata.usage_count += 1
            await self.storage.write("knowledge", entry.id, entry.to_dict())
