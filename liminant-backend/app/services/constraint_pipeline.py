from typing import Any


class ConstraintPipeline:
    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        stage1 = await self._stage1_input_analysis(input_data)
        stage2 = await self._stage2_kb_retrieval(stage1)
        stage3 = await self._stage3_constraint_application(stage2)
        stage4 = await self._stage4_output_optimization(stage3)
        return stage4

    async def _stage1_input_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        user_input = data.get("user_input", "")
        session = data.get("session", {})

        is_vibal = user_input.strip().startswith(".")
        intent = self._extract_intent(user_input)

        return {
            **data,
            "stage": 1,
            "intent": intent,
            "is_vibal_command": is_vibal,
            "requirements": self._extract_requirements(user_input),
        }

    async def _stage2_kb_retrieval(self, data: dict[str, Any]) -> dict[str, Any]:
        from app.agents.librarian import LibrarianAgent
        librarian = LibrarianAgent()

        session = data.get("session", {})
        user_input = data.get("user_input", "")

        intent_query = data.get("intent", "") + " " + user_input
        kb_results = await librarian.run({"query": intent_query, "session": session, "limit": 5})

        session_triggered = await librarian.kb.trigger_for_session(session)

        all_entries = kb_results.get("results", []) + [
            e for e in session_triggered if e.id not in [r["id"] for r in kb_results.get("results", [])]
        ]

        return {
            **data,
            "stage": 2,
            "kb_entries": all_entries,
            "kb_count": len(all_entries),
            "session_triggered_count": len(session_triggered),
        }

    async def _stage3_constraint_application(self, data: dict[str, Any]) -> dict[str, Any]:
        kb_entries = data.get("kb_entries", [])
        context = data.get("session", {}).get("context", {})

        applied_constraints = []
        for entry in kb_entries:
            if self._is_applicable(entry, context):
                applied_constraints.append(entry)

        return {
            **data,
            "stage": 3,
            "applied_constraints": applied_constraints,
            "constraint_count": len(applied_constraints),
        }

    async def _stage4_output_optimization(self, data: dict[str, Any]) -> dict[str, Any]:
        applied_constraints = data.get("applied_constraints", [])
        original_output = data.get("response", "")

        optimized = original_output
        if applied_constraints and original_output:
            constraint_bodies = [e.get("content", {}).get("body", "") for e in applied_constraints]
            if constraint_bodies:
                optimization_note = (
                    f"\n\n---\n*Optimized with {len(constraint_bodies)} constraint(s) from knowledge base.*"
                )
                optimized = original_output + optimization_note

        return {
            **data,
            "stage": 4,
            "response": optimized,
            "pipeline_complete": True,
        }

    async def record_effectiveness(self, applied_constraint_ids: list[str], response_quality: str) -> None:
        from app.services.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        positive = response_quality in ("good", "helpful", "accepted")
        for cid in applied_constraint_ids:
            await kb.record_outcome(cid, positive)

    def _extract_intent(self, text: str) -> str:
        text = text.strip()
        if text.startswith("."):
            parts = text.split()
            return parts[0] if parts else "unknown"
        if any(kw in text.lower() for kw in ["write", "create", "make", "generate"]):
            return "code_generation"
        if any(kw in text.lower() for kw in ["explain", "what", "how", "why"]):
            return "explanation"
        if any(kw in text.lower() for kw in ["list", "show", "display"]):
            return "listing"
        if any(kw in text.lower() for kw in ["fix", "bug", "error", "issue"]):
            return "debugging"
        if any(kw in text.lower() for kw in ["refactor", "optimize", "improve"]):
            return "refactoring"
        return "general"

    def _extract_requirements(self, text: str) -> list[str]:
        import re
        reqs = re.findall(r'"([^"]*)"|' r"'([^']*)'", text)
        return [r[0] or r[1] for r in reqs]

    def _is_applicable(self, entry: dict[str, Any], context: dict[str, Any]) -> bool:
        entry_type = entry.get("type", "")
        tags = entry.get("metadata", {}).get("tags", [])
        working_dir = context.get("working_directory", "")

        if entry_type == "rule":
            return True
        if entry_type == "pattern":
            return any(t in working_dir.lower() for t in tags)
        return True
