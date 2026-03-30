from typing import Any
from app.agents.base import BaseAgent
from app.services.knowledge_base import KnowledgeBase


class LibrarianAgent(BaseAgent):
    def __init__(self, agent_id: str = "librarian"):
        super().__init__(agent_id, "librarian")
        self.kb = KnowledgeBase()

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        self.set_state("thinking", "Searching knowledge base", 0.1)

        query = input_data.get("query", "")
        session = input_data.get("session", {})
        limit = input_data.get("limit", 5)

        self.set_state("executing", "Ranking knowledge entries", 0.5)

        results = await self.kb.search(query=query, limit=limit)

        for entry in results:
            await self.kb.increment_usage(entry.id)

        self.set_state("idle", "Done", 1.0)

        return {
            "results": [e.to_dict() for e in results],
            "count": len(results),
            "query": query,
        }

    async def get_context_for_session(self, session: dict[str, Any]) -> list[dict[str, Any]]:
        self.set_state("thinking", "Loading session context from KB", 0.1)

        constraints = session.get("constraints", {})
        knowledge_refs = constraints.get("knowledge_refs", [])
        rules = constraints.get("rules", [])

        results = []
        for kb_id in knowledge_refs:
            entry = await self.kb.get(kb_id)
            if entry:
                results.append(entry.to_dict())

        for rule_id in rules:
            entry = await self.kb.get(rule_id)
            if entry:
                results.append(entry.to_dict())

        self.set_state("idle", "Done", 1.0)
        return results
