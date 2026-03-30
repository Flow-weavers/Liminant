import re
from typing import Any
from app.agents.base import BaseAgent


class ContextParserAgent(BaseAgent):
    VIBAL_PATTERN = re.compile(r"^\.(\w+)(?:\s+(.+?))?(?:\s+--(\S+?)(?:\[([^\]]*)\])?)?$")

    def __init__(self, agent_id: str = "context_parser"):
        super().__init__(agent_id, "context_parser")

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        self.set_state("thinking", "Parsing vibal command", 0.1)

        raw = input_data.get("raw", "")
        context = input_data.get("context", {})

        parsed = self._parse_command(raw)

        self.set_state("executing", "Generating context report", 0.5)

        if not parsed["command"]:
            return {"response": "No vibal command detected.", "parsed": parsed, "report": None}

        report = await self._generate_report(parsed, context)

        self.set_state("idle", "Done", 1.0)

        return {
            "response": report,
            "parsed": parsed,
            "report": report,
        }

    def _parse_command(self, raw: str) -> dict[str, Any]:
        match = self.VIBAL_PATTERN.match(raw.strip())
        if not match:
            return {"command": None, "target": raw, "flag": None, "flag_value": None}

        command, target, flag, flag_value = match.groups()
        return {
            "command": command,
            "target": target or "",
            "flag": flag,
            "flag_value": flag_value,
        }

    async def _generate_report(self, parsed: dict[str, Any], context: dict[str, Any]) -> str:
        command = parsed["command"]
        target = parsed["target"]
        flag = parsed["flag"]
        flag_value = parsed["flag_value"] or ""

        if command == "list":
            if target == "changes":
                return await self._list_changes(flag_value, context)
            elif target == "session":
                return await self._list_session(context)
            elif target == "artifacts":
                return await self._list_artifacts(flag_value, context)
        elif command == "explain":
            return await self._explain(target, flag_value, context)
        elif command == "summarize":
            return await self._summarize(flag_value, context)
        elif command == "diff":
            return await self._diff(target, flag_value, context)

        return f"Unknown vibal command: .{command}"

    async def _list_changes(self, level: str, context: dict[str, Any]) -> str:
        sentences = int(level) if level.isdigit() else 2
        session = context.get("session", {})
        messages = session.get("messages", [])

        changes = [m for m in messages if m.get("role") == "assistant" and m.get("content")]
        if not changes:
            return "No changes recorded in this session."

        lines = [f"**Session Changes Summary** ({len(changes)} assistant responses)\n"]
        for i, m in enumerate(changes[-5:], 1):
            content = m["content"]
            preview = content[:200] + "..." if len(content) > 200 else content
            lines.append(f"{i}. {preview}")

        lines.append(f"\n_Showing {min(5, len(changes))} of {len(changes)} responses, ~{sentences} sentences each requested._")
        return "\n".join(lines)

    async def _list_session(self, context: dict[str, Any]) -> str:
        session = context.get("session", {})
        messages = session.get("messages", [])
        return (
            f"**Session Overview**\n"
            f"- ID: `{session.get('id', 'unknown')}`\n"
            f"- Phase: {session.get('state', {}).get('phase', 'unknown')}\n"
            f"- Messages: {len(messages)}\n"
            f"- Working dir: `{session.get('context', {}).get('working_directory', '/')}`"
        )

    async def _list_artifacts(self, level: str, context: dict[str, Any]) -> str:
        session = context.get("session", {})
        artifacts = session.get("artifacts", [])
        if not artifacts:
            return "No artifacts generated in this session."
        lines = ["**Artifacts**\n"]
        for a in artifacts:
            lines.append(f"- `{a.get('path', 'unknown')}` — {a.get('summary', 'no summary')} ({a.get('type', 'file')})")
        return "\n".join(lines)

    async def _explain(self, target: str, scope: str, context: dict[str, Any]) -> str:
        messages = context.get("session", {}).get("messages", [])
        if not messages:
            return "No context to explain."

        system = next((m for m in messages if m.get("role") == "system"), None)
        user_msgs = [m for m in messages if m.get("role") == "user"]
        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]

        return (
            f"**Context Explanation**\n"
            f"- System messages: {len(system) if system else 0}\n"
            f"- User messages: {len(user_msgs)}\n"
            f"- Assistant responses: {len(assistant_msgs)}\n"
            f"- Current target: {target or 'general'}\n"
            f"- Scope: {scope or 'recent'}"
        )

    async def _summarize(self, length: str, context: dict[str, Any]) -> str:
        msg_count = len(context.get("session", {}).get("messages", []))
        word_count = sum(
            len(m.get("content", "").split())
            for m in context.get("session", {}).get("messages", [])
        )
        return (
            f"**Session Summary**\n"
            f"- Total messages: {msg_count}\n"
            f"- Approx. words: {word_count}\n"
            f"- Detail level: {length or 'medium'}"
        )

    async def _diff(self, target: str, diff_type: str, context: dict[str, Any]) -> str:
        artifacts = context.get("session", {}).get("artifacts", [])
        if not artifacts:
            return "No diffs available — no artifacts generated yet."
        lines = ["**Diff Report**\n"]
        for a in artifacts:
            for change in a.get("changes", []):
                lines.append(f"```diff\n{change.get('diff', 'No diff available')}\n```")
        return "\n".join(lines) if len(lines) > 1 else "No changes recorded."
