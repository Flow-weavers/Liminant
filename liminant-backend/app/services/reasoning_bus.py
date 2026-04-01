import re
from typing import Any
from app.agents.base import BaseAgent
from app.agents.context_parser import ContextParserAgent
from app.agents.librarian import LibrarianAgent
from app.agents.coder import CoderAgent
from app.services.constraint_pipeline import ConstraintPipeline
from app.services.reasoning_context import ReasoningContext, PipelinePhase
from app.services.llm_driver import LLMDriver
from app.services.pipeline_event_bus import PipelineEventBus


class ReasoningBus:
    VIBAL_PATTERN = re.compile(r"^\.\w+")

    def __init__(self):
        self.context_parser = ContextParserAgent()
        self.librarian = LibrarianAgent()
        self.coder = CoderAgent()
        self.pipeline = ConstraintPipeline()
        self.llm_driver = LLMDriver()
        self._bus = PipelineEventBus.get_instance()

    async def drive(self, user_input: str, messages: list[dict], session: dict[str, Any], context_filter: list[str] | None = None) -> ReasoningContext:
        ctx = ReasoningContext(
            user_input=user_input,
            session_id=session.get("id", ""),
            working_directory=session.get("context", {}).get("working_directory", "/workspace/default"),
            language=session.get("context", {}).get("language", "en-US"),
        )

        is_vibal = bool(self.VIBAL_PATTERN.match(user_input.strip()))
        ctx.is_vibal_command = is_vibal

        if is_vibal:
            ctx.phase = PipelinePhase.GENERATING
            cp_result = await self.context_parser.run({"raw": user_input, "context": {
                "session": session,
                "working_directory": ctx.working_directory,
                "language": ctx.language,
            }})
            ctx.vibal_response = cp_result.get("response", "")
            ctx.response_text = ctx.vibal_response
            ctx.pipeline_stage = 4
            ctx.pipeline_complete = True
            return ctx

        ctx.phase = PipelinePhase.ABSORBING
        ctx = await self._absorb(ctx, user_input, session, context_filter)
        self._bus.emit(ctx.session_id, "absorbing", 1, {
            "intent": ctx.intent,
            "requirements": ctx.requirements,
            "kb_entries": ctx.kb_entries,
        })

        ctx.phase = PipelinePhase.CONSTRAINING
        ctx = await self._constrain(ctx, user_input, session)
        self._bus.emit(ctx.session_id, "constraining", 2, {
            "applied_constraints": ctx.applied_constraints,
        })

        ctx.phase = PipelinePhase.GENERATING
        ctx = await self._generate(ctx, messages, session)
        self._bus.emit(ctx.session_id, "generating", 3, {
            "response_preview": ctx.response_text[:200] if ctx.response_text else "",
            "artifacts": ctx.artifacts,
            "tools_used": ctx.tools_used,
        })

        ctx.phase = PipelinePhase.VALIDATING
        ctx = await self._validate(ctx)
        self._bus.emit(ctx.session_id, "validating", 4, {
            "optimization_notes": ctx.optimization_notes,
        })

        ctx.phase = PipelinePhase.DONE
        ctx.pipeline_complete = True
        return ctx

    async def _absorb(self, ctx: ReasoningContext, user_input: str, session: dict, context_filter: list[str] | None = None) -> ReasoningContext:
        pipeline_data = await self.pipeline.run({
            "user_input": user_input,
            "session": session,
            "context_filter": context_filter,
        })
        ctx.intent = pipeline_data.get("intent", "general")
        ctx.requirements = pipeline_data.get("requirements", [])
        ctx.kb_entries = pipeline_data.get("kb_entries", [])
        ctx.pipeline_stage = 1
        return ctx

    async def _constrain(self, ctx: ReasoningContext, user_input: str, session: dict) -> ReasoningContext:
        applied = []
        for entry in ctx.kb_entries:
            if self._is_applicable(entry, session.get("context", {})):
                applied.append(entry)
        ctx.applied_constraints = applied
        ctx.pipeline_stage = 2
        return ctx

    async def _generate(self, ctx: ReasoningContext, messages: list[dict], session: dict) -> ReasoningContext:
        if ctx.intent == "code_generation" and not ctx.is_vibal_command:
            coder_result = await self.coder.run({
                "request": ctx.user_input,
                "context": {
                    "session": session,
                    "working_directory": ctx.working_directory,
                    "language": ctx.language,
                },
                "constraints": ctx.applied_constraints,
            })

            if coder_result.get("path") and coder_result.get("code"):
                from app.services.tool_executor import ToolExecutor
                from app.config import settings
                te = ToolExecutor(allowed_paths=settings.tool_allowed_paths)
                result = await te.execute("file_write", {
                    "path": coder_result["path"],
                    "content": coder_result["code"],
                })
                if result.get("success"):
                    ctx.generated_path = coder_result["path"]
                    ctx.generated_code = coder_result["code"]
                    diff = coder_result.get("diff", "")
                    ctx.response_text = (
                        f"File written to `{coder_result['path']}`\n\n"
                        f"```diff\n{diff}\n```\n\n"
                        f"_Generated with {len(ctx.applied_constraints)} active constraint(s)._"
                    )
                    artifact = coder_result.get("artifacts", [{}])[0] if coder_result.get("artifacts") else {}
                    ctx.artifacts = [artifact]
                    ctx.pipeline_stage = 3
                    return ctx

        ctx = await self.llm_driver.run(ctx, messages)
        ctx.pipeline_stage = 3
        return ctx

    async def _validate(self, ctx: ReasoningContext) -> ReasoningContext:
        if ctx.applied_constraints and ctx.response_text:
            note = (
                f"\n\n---\n*Optimized with {len(ctx.applied_constraints)} constraint(s) from knowledge base.*"
            )
            ctx.response_text += note
            ctx.optimization_notes.append(note)
        ctx.pipeline_stage = 4
        return ctx

    async def record_effectiveness(self, constraint_ids: list[str], quality: str) -> None:
        await self.pipeline.record_effectiveness(constraint_ids, quality)

    async def refresh_session_constraints(self, session: dict[str, Any]) -> None:
        if not session.get("constraints", {}).get("active", False):
            return
        try:
            triggered = await self.librarian.kb.trigger_for_session(session)
            for entry in triggered:
                if entry.id not in session.get("constraints", {}).get("knowledge_refs", []):
                    session["constraints"]["knowledge_refs"].append(entry.id)
        except Exception:
            pass

    def _is_applicable(self, entry: dict, context: dict) -> bool:
        entry_type = entry.get("type", "rule")
        if entry_type in ("pattern", "standard"):
            return True
        body = entry.get("content", {}).get("body", "").lower()
        ctx_lang = context.get("language", "en-US").lower()
        if "chinese" in body or "中文" in body:
            return "zh" in ctx_lang
        if "english" in body or "英文" in body:
            return "en" in ctx_lang
        return True
