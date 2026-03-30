import difflib
from typing import Any
from app.agents.base import BaseAgent
from app.config import settings


class CoderAgent(BaseAgent):
    def __init__(self, agent_id: str = "coder"):
        super().__init__(agent_id, "coder")
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature
        self.max_tokens = settings.openai_max_tokens

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        self.set_state("thinking", "Analyzing code request", 0.1)

        request = input_data.get("request", "")
        context = input_data.get("context", {})
        constraints = input_data.get("constraints", [])
        working_dir = context.get("working_directory", "/workspace/default")

        self.set_state("executing", "Generating code", 0.5)

        code_output = await self._generate_code(request, context, constraints)

        diff = ""
        if code_output.get("path"):
            diff = await self._compute_diff(
                code_output.get("original", ""),
                code_output.get("content", ""),
                code_output.get("path", ""),
            )

        self.set_state("idle", "Done", 1.0)

        return {
            "code": code_output.get("content", ""),
            "path": code_output.get("path", ""),
            "language": code_output.get("language", "python"),
            "diff": diff,
            "artifacts": [
                {
                    "id": f"art_{id(self)}",
                    "type": "code",
                    "path": code_output.get("path", ""),
                    "summary": f"Generated {code_output.get('language', 'code')} file",
                    "changes": [
                        {
                            "type": "create",
                            "description": f"Generated from request: {request[:50]}",
                            "diff": diff,
                        }
                    ],
                }
            ],
        }

    async def _generate_code(self, request: str, context: dict, constraints: list) -> dict[str, Any]:
        constraint_text = "\n".join([f"- {c.get('content', {}).get('body', str(c))}" for c in constraints[:3]])

        prompt = (
            f"You are the Coder SubAgent in the Liminal platform.\n"
            f"Working directory: {context.get('working_directory', '/workspace/default')}\n"
            f"Language preference: {context.get('language', 'en-US')}\n"
            f"Active constraints:\n{constraint_text or 'No active constraints.'}\n\n"
            f"Request: {request}\n\n"
            f"Respond ONLY with a valid JSON object with these keys: path, content (the full code), language.\n"
            f'Example: {{"path": "/workspace/test.py", "content": "print(\'hello\')", "language": "python"}}'
        )

        api_key = settings.openai_api_key
        if not api_key:
            return {"path": "", "content": "", "language": "python"}

        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key, base_url=settings.openai_base_url)
            completion = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=2000,
            )
            import json, re
            text = completion.choices[0].message.content or "{}"
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                return json.loads(match.group())
        except Exception:
            pass

        return {"path": "", "content": "", "language": "python"}

    async def _compute_diff(self, original: str, new: str, path: str) -> str:
        if not original:
            return f"--- /dev/null\n+++ {path}\n@@ -0,0 +1,{new.count(chr(10))+1} @@\n" + "\n".join(f"+{line}" for line in new.splitlines())

        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            lineterm="",
        )
        return "".join(diff)
