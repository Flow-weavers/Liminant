from typing import Any
from app.agents.base import BaseAgent
from app.services.reasoning_bus import ReasoningBus


class CoordinatorAgent(BaseAgent):
    def __init__(self, agent_id: str = "coordinator"):
        super().__init__(agent_id, "coordinator")
        self.bus = ReasoningBus()

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        messages = input_data.get("messages", [])
        session = input_data.get("session", {})
        user_input = messages[-1]["content"] if messages else ""
        context_filter = input_data.get("context_filter")

        self.set_state("thinking", "Driving reasoning bus", 0.1)

        ctx = await self.bus.drive(user_input, messages, session, context_filter)

        if ctx.applied_constraints:
            quality = "good" if len(ctx.response_text) > 50 else "neutral"
            await self.bus.record_effectiveness(
                [c.get("id", "") for c in ctx.applied_constraints],
                quality,
            )

        await self.bus.refresh_session_constraints(session)

        self.set_state("idle", "Done", 1.0)

        applied_ids = [c.get("id", "") for c in ctx.applied_constraints]

        response = ctx.response_text
        if not response:
            response = f"[No response — phase={ctx.phase.value} stage={ctx.pipeline_stage} error={ctx.error!r}]"

        return {
            "response": response,
            "tools_used": ctx.tools_used,
            "artifacts": ctx.artifacts,
            "reasoning": ctx.to_dict(),
            "phase": ctx.phase.value,
            "applied_constraint_ids": applied_ids,
        }
