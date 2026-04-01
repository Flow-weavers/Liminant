import json
from app.config import settings
from app.services.tool_executor import ToolExecutor
from app.services.pipeline_event_bus import PipelineEventBus

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "file_read",
            "description": "Read the complete contents of a file from the filesystem.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative path to the file to read."}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_write",
            "description": "Write or overwrite content to a file. Creates parent directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Target file path."},
                    "content": {"type": "string", "description": "Full file content to write."},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a PowerShell command (Windows) or shell command (Unix) and return its stdout/stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command to execute. Use PowerShell syntax on Windows."},
                    "cwd": {"type": "string", "description": "Optional working directory."},
                },
                "required": ["command"],
            },
        },
    },
]


class LLMDriver:
    MAX_ITERATIONS = 5

    def __init__(self):
        self.tool_executor = ToolExecutor(allowed_paths=settings.tool_allowed_paths)
        self._bus = PipelineEventBus.get_instance()

    def _build_system_prompt(self, ctx: "ReasoningContext") -> str:
        parts = [
            "You are the Coordinator Agent in the Liminal Vibe Engineering platform.",
            "You help users accomplish tasks through specialized SubAgents.",
            "You have access to file_read, file_write, and bash tools.",
            "Use tools whenever the user asks you to read, write, or execute anything.",
            "Be concise and action-oriented.",
        ]

        if ctx.kb_entries:
            parts.append("\nActive knowledge base constraints:")
            for e in ctx.kb_entries[:5]:
                e_type = e.get("type", "rule")
                e_title = e.get("content", {}).get("title", "Untitled")
                e_body = e.get("content", {}).get("body", "")
                parts.append(f"- `[{e_type}]` **{e_title}**: {e_body[:100]}...")

        if ctx.applied_constraints:
            parts.append(f"\n{len(ctx.applied_constraints)} constraint(s) applied by the pipeline.")

        return "\n".join(parts)

    async def run(self, ctx: "ReasoningContext", messages: list[dict]) -> "ReasoningContext":
        import logging
        logger = logging.getLogger(__name__)

        api_key = settings.openai_api_key
        if not api_key:
            ctx.response_text = (
                "Coordinator is ready. Configure `OPENAI_API_KEY` to enable LLM responses.\n\n"
                f"Request received: {ctx.user_input[:100]}\n"
                f"KB entries found: {len(ctx.kb_entries)}"
            )
            return ctx

        constraint_lines = []
        if ctx.kb_entries:
            constraint_lines = ["Active knowledge base constraints:"]
            for e in ctx.kb_entries[:5]:
                e_type = e.get("type", "rule")
                e_title = e.get("content", {}).get("title", "Untitled")
                e_body = e.get("content", {}).get("body", "")
                constraint_lines.append(f"- `[{e_type}]` **{e_title}**: {e_body[:80]}...")

        system_prompt = (
            "You are the Coordinator Agent in the Liminal Vibe Engineering platform. "
            "You help users accomplish tasks through specialized SubAgents. "
            "You have access to file_read, file_write, and bash tools. "
            "Use tools whenever the user asks you to read, write, or execute anything. "
            "Be concise and action-oriented.\n\n"
            f"Working directory: {ctx.working_directory}\n"
            f"Language: {ctx.language}\n\n"
            + ("\n".join(constraint_lines) + "\n\n" if constraint_lines else "")
        )

        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key, base_url=settings.openai_base_url)

            conversation = [{"role": "system", "content": system_prompt}] + list(messages)
            tools_used: list[dict] = []

            for iteration in range(self.MAX_ITERATIONS):
                logger.debug(f"LLMDriver iteration {iteration + 1}: calling OpenAI")
                completion = await client.chat.completions.create(
                    model=settings.openai_model,
                    messages=conversation,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    temperature=settings.openai_temperature,
                    max_tokens=settings.openai_max_tokens,
                )
                choice = completion.choices[0]
                reply = choice.message

                if not reply.tool_calls:
                    raw = reply.content
                    if raw:
                        ctx.response_text = raw
                    elif tools_used:
                        ctx.response_text = f"[{len(tools_used)} tool(s) executed — no text response]"
                    else:
                        ctx.response_text = "Coordinator processed your request."
                    ctx.tools_used = tools_used
                    ctx.phase = ctx.phase.DONE
                    return ctx

                conversation.append(reply.model_dump(include={"role", "content", "tool_calls"}))

                for tc in reply.tool_calls:
                    tool_name = tc.function.name
                    args = {}
                    try:
                        args = json.loads(tc.function.arguments)
                    except Exception:
                        pass

                    result = await self.tool_executor.execute(tool_name, args)
                    tools_used.append({"name": tool_name, "args": args, "result": result})
                    self._bus.emit(ctx.session_id, "tool_executed", 3, {
                        "tool_name": tool_name,
                        "args": {k: v for k, v in args.items() if k != "content"},
                        "result": result,
                    })

                    conversation.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })

                logger.debug(f"LLMDriver iteration {iteration + 1}: {len(reply.tool_calls)} tool calls executed")

            last_reply = completion.choices[0].message
            raw = last_reply.content
            if raw:
                ctx.response_text = raw
            elif tools_used:
                ctx.response_text = f"[{len(tools_used)} tool(s) executed — no text response]"
            else:
                ctx.response_text = "Coordinator processed your request."
            ctx.tools_used = tools_used
            ctx.phase = ctx.phase.DONE
            return ctx

        except Exception as e:
            ctx.error = str(e)
            ctx.phase = ctx.phase.DONE
            return ctx

    async def complete(self, prompt: str, system: str = "") -> str:
        import logging
        logger = logging.getLogger(__name__)

        api_key = settings.openai_api_key
        if not api_key:
            return '{"entries": []}'

        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
            )
            return response.choices[0].message.content or '{"entries": []}'
        except Exception as e:
            logger.error(f"LLMDriver.complete failed: {e}")
            return '{"entries": []}'
