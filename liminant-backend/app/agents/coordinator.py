import re
from typing import Any
from app.agents.base import BaseAgent
from app.agents.context_parser import ContextParserAgent
from app.agents.librarian import LibrarianAgent
from app.agents.coder import CoderAgent
from app.services.constraint_pipeline import ConstraintPipeline
from app.services.tool_executor import ToolExecutor
from app.config import settings


class CoordinatorAgent(BaseAgent):
    VIBAL_PATTERN = re.compile(r"^\.\w+")

    def __init__(self, agent_id: str = "coordinator"):
        super().__init__(agent_id, "coordinator")
        self.context_parser = ContextParserAgent()
        self.librarian = LibrarianAgent()
        self.coder = CoderAgent()
        self.pipeline = ConstraintPipeline()
        self.tool_executor = ToolExecutor(allowed_paths=settings.tool_allowed_paths)

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        self.set_state("thinking", "Analyzing request", 0.1)

        messages = input_data.get("messages", [])
        session = input_data.get("session", {})
        user_input = messages[-1]["content"] if messages else ""
        is_vibal = bool(self.VIBAL_PATTERN.match(user_input.strip()))

        context = {
            "session": session,
            "working_directory": session.get("context", {}).get("working_directory", "/workspace/default"),
            "language": session.get("context", {}).get("language", "en-US"),
        }

        if is_vibal:
            self.set_state("executing", "Delegating to ContextParser", 0.3)
            cp_result = await self.context_parser.run({"raw": user_input, "context": context})
            return await self._finish_response(cp_result.get("response", ""), session, [])

        self.set_state("executing", "Running constraint pipeline", 0.2)
        pipeline_data = await self.pipeline.run({
            "user_input": user_input,
            "session": session,
        })

        kb_entries = pipeline_data.get("kb_entries", [])
        applied_constraints = pipeline_data.get("applied_constraints", [])

        intent = pipeline_data.get("intent", "general")
        is_code_request = intent == "code_generation"

        if is_code_request:
            self.set_state("executing", "Delegating to Coder", 0.5)
            coder_result = await self.coder.run({
                "request": user_input,
                "context": context,
                "constraints": applied_constraints,
            })

            if coder_result.get("path") and coder_result.get("code"):
                tool_result = await self.tool_executor.execute("file_write", {
                    "path": coder_result["path"],
                    "content": coder_result["code"],
                })
                if tool_result.get("success"):
                    artifact = coder_result["artifacts"][0] if coder_result.get("artifacts") else {}
                    artifact["changes"][0]["type"] = "create"
                    response_text = (
                        f"File written to `{coder_result['path']}`\n\n"
                        f"```diff\n{coder_result.get('diff', '')}\n```\n\n"
                        f"_Generated with {len(applied_constraints)} active constraints._"
                    )
                    return await self._finish_response(response_text, session, [artifact])

        self.set_state("executing", "Calling LLM for response", 0.6)
        llm_response = await self._call_llm(user_input, messages, context, kb_entries)

        return await self._finish_response(llm_response, session, [])

    async def _call_llm(
        self, user_input: str, messages: list[dict], context: dict, kb_entries: list[dict]
    ) -> str:
        api_key = settings.openai_api_key
        if not api_key:
            return (
                "Coordinator is ready. Configure `OPENAI_API_KEY` to enable LLM responses.\n\n"
                f"Request received: {user_input[:100]}\n"
                f"KB entries found: {len(kb_entries)}"
            )

        constraint_text = ""
        if kb_entries:
            lines = ["Active knowledge base constraints:"]
            for e in kb_entries[:3]:
                lines.append(f"- [{e.get('type', 'rule')}] {e.get('content', {}).get('title', 'Untitled')}")
            constraint_text = "\n".join(lines)

        system_prompt = (
            "You are the Coordinator Agent in the Liminal Vibe Engineering platform. "
            "You help users accomplish tasks through specialized SubAgents. "
            "You have access to file_read, file_write, and bash tools. "
            "Be concise and action-oriented.\n\n"
            f"Current context:\n"
            f"- Working directory: {context.get('working_directory', '/workspace/default')}\n"
            f"- Language: {context.get('language', 'en-US')}\n\n"
            + (constraint_text + "\n\n" if constraint_text else "")
        )

        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            all_messages = [{"role": "system", "content": system_prompt}] + messages
            completion = await client.chat.completions.create(
                model=settings.openai_model,
                messages=all_messages,
                temperature=settings.openai_temperature,
                max_tokens=settings.openai_max_tokens,
            )
            return completion.choices[0].message.content or ""
        except Exception as e:
            return f"Error calling LLM: {str(e)}"

    async def _finish_response(
        self, response_text: str, session: dict, artifacts: list[dict]
    ) -> dict[str, Any]:
        self.set_state("idle", "Done", 1.0)
        return {
            "response": response_text,
            "tools_used": [],
            "artifacts": artifacts,
        }
