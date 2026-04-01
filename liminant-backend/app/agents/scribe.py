from typing import Any
from app.agents.base import BaseAgent
from app.services.knowledge_base import KnowledgeBase
from app.models.knowledge import KnowledgeType, KnowledgeCreate


SCRIBE_PROMPT = """You are Scribe, a knowledge engineer embedded in the Liminal reasoning system.

Your job is to read a conversation between a user and an AI assistant, then extract generalizable knowledge from it.

Given the following interaction:

User request: {user_input}
Assistant response: {assistant_response}
Artifacts created: {artifacts}
Applied constraints ({constraint_count}): {constraints}

Extract 0-3 knowledge entries that capture reusable patterns or rules from this interaction.

For each entry you propose, return a JSON object with:
- "type": one of "rule", "pattern", "preference", "context"
- "title": a short, descriptive title (max 8 words)
- "body": the core knowledge statement (1-3 sentences)
- "keywords": 2-5 trigger keywords for future retrieval
- "confidence": a float 0.1-0.6 (scribe proposals start low — they need human validation)
- "trigger_reason": why this interaction revealed this knowledge

Rules:
- Only propose entries that represent genuinely generalizable knowledge, not one-off facts
- confidence should be LOW (0.1-0.6) because these are unverified inferences
- keywords should be practical: what would someone type to activate this knowledge?
- If no generalizable knowledge can be extracted, return an empty list
- body should capture the "why" not just the "what"

Return a JSON object with an "entries" key containing your proposed entries, or {"entries": []} if nothing worth capturing."""


class ScribeAgent(BaseAgent):
    TRIGGER_FEEDBACK = ["actually", "should", "prefer", "instead", "wrong", "not quite", "issue", "problem", "however"]
    TRIGGER_ARTIFACT = ["good", "helpful", "great", "works", "accepted", "thanks"]
    MIN_RESPONSE_LEN = 100

    def __init__(self, agent_id: str = "scribe"):
        super().__init__(agent_id, "scribe")
        self.kb = KnowledgeBase()

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        user_input = input_data.get("user_input", "")
        assistant_response = input_data.get("assistant_response", "")
        artifacts = input_data.get("artifacts", [])
        applied_constraints = input_data.get("applied_constraints", [])
        session = input_data.get("session", {})
        trigger = input_data.get("trigger", "none")

        self.set_state("thinking", "Analyzing interaction for extractable knowledge", 0.2)

        if not self._should_trigger(user_input, assistant_response, artifacts, trigger):
            return {"entries": [], "trigger": trigger, "reason": "insufficient_signal"}

        self.set_state("executing", "Generating knowledge candidates", 0.5)

        prompt = self._build_prompt(user_input, assistant_response, artifacts, applied_constraints)

        from app.services.llm_driver import LLMDriver
        driver = LLMDriver()
        raw = await driver.complete(prompt, system="You are a JSON-only machine. Output only valid JSON, no markdown fences or commentary.")

        entries = self._parse_entries(raw)

        self.set_state("idle", "Done", 1.0)

        return {
            "entries": entries,
            "trigger": trigger,
            "count": len(entries),
        }

    def _should_trigger(self, user_input: str, assistant_response: str, artifacts: list, trigger: str) -> bool:
        if trigger == "feedback":
            return True
        if trigger == "artifact" and len(artifacts) > 0:
            return True
        if trigger == "pattern" and len(assistant_response) >= self.MIN_RESPONSE_LEN:
            return True
        return False

    def _build_prompt(self, user_input: str, assistant_response: str, artifacts: list, applied_constraints: list) -> str:
        artifact_str = "\n".join([
            f"- {a.get('type', 'file')}: {a.get('path', a.get('id', 'unknown'))}"
            for a in artifacts
        ]) or "None"

        constraint_str = "\n".join([
            f"- {c.get('title', c.get('id', 'unknown'))}"
            for c in applied_constraints
        ]) or "None"

        return SCRIBE_PROMPT.format(
            user_input=user_input,
            assistant_response=assistant_response[:2000] if assistant_response else "(empty)",
            artifacts=artifact_str,
            constraint_count=len(applied_constraints),
            constraints=constraint_str,
        )

    def _parse_entries(self, raw: str) -> list[dict[str, Any]]:
        try:
            import json, re
            cleaned = re.sub(r"```json\s*", "", raw, flags=re.IGNORECASE).strip()
            cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.IGNORECASE).strip()
            data = json.loads(cleaned)
            raw_entries = data.get("entries", [])
            if not isinstance(raw_entries, list):
                return []
            results = []
            for e in raw_entries:
                if not all(k in e for k in ("type", "title", "body", "keywords")):
                    continue
                results.append({
                    "type": e["type"],
                    "title": e["title"],
                    "body": e["body"],
                    "keywords": e.get("keywords", []),
                    "confidence": float(e.get("confidence", 0.3)),
                    "trigger_reason": e.get("trigger_reason", ""),
                })
            return results
        except Exception:
            return []

    async def propose_and_save(self, input_data: dict[str, Any]) -> list[str]:
        result = await self.run(input_data)
        saved_ids = []
        for entry in result.get("entries", []):
            try:
                created = await self.kb.create(KnowledgeCreate(
                    type=KnowledgeType(entry["type"]),
                    title=entry["title"],
                    body=entry["body"],
                    keywords=entry["keywords"],
                ))
                entry_id = created.id
                await self.kb.update(entry_id, {
                    "metadata": {
                        **created.metadata.__dict__,
                        "confidence": entry["confidence"],
                        "source": "scribe_inferred",
                        "pending_review": True,
                    }
                })
                saved_ids.append(entry_id)
            except Exception:
                pass
        return saved_ids
