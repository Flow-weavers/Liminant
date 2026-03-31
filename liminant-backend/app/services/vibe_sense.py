import re
from typing import Any


class VibeSense:
    VIBAL = re.compile(r"^\.(\w+)(?:\s+(.+?))?(?:\s+--(\S+?)(?:\[([^\]]*)\])?)?$")
    INTENT_KEYWORDS = {
        "code_generation": ["write", "create", "make", "generate", "build", "implement", "add"],
        "explanation": ["explain", "what", "how", "why", "describe", "tell me"],
        "listing": ["list", "show", "display", "find", "search", "get"],
        "modification": ["change", "modify", "update", "edit", "refactor", "fix"],
        "deletion": ["delete", "remove", "drop", "clear"],
        "execution": ["run", "execute", "start", "stop", "deploy"],
    }
    CONTEXT_HINTS = re.findall(r'"([^"]+)"|' r"'([^']+)'", "")
    METADATA_PATTERNS = [
        (re.compile(r"--(\w+)\[([^\]]*)\]"), "flag_value"),
        (re.compile(r"--(\w+)"), "flag"),
        (re.compile(r"\[~?(\d+)\s*(?:sentences?|words?|chars?)\]"), "level"),
        (re.compile(r"\[(\w+)\]"), "inline_modifier"),
    ]

    def analyze(self, text: str) -> dict[str, Any]:
        text = text.strip()

        is_vibal = bool(self.VIBAL.match(text))
        vibal_parsed = self._parse_vibal(text) if is_vibal else None
        intent = self._classify_intent(text) if not is_vibal else vibal_parsed["command"] if vibal_parsed else "unknown"
        modifiers = self._extract_modifiers(text)
        suggested_actions = self._get_suggested_actions(intent, modifiers)
        confidence = self._calculate_confidence(text, intent, is_vibal)

        return {
            "raw": text,
            "is_vibal_command": is_vibal,
            "intent": intent,
            "vibal_parsed": vibal_parsed,
            "modifiers": modifiers,
            "suggested_actions": suggested_actions,
            "confidence": confidence,
            "token_estimate": len(text.split()),
        }

    def _parse_vibal(self, text: str) -> dict[str, Any] | None:
        match = self.VIBAL.match(text)
        if not match:
            return None
        command, target, flag, flag_value = match.groups()
        return {
            "command": command,
            "target": target or "",
            "flag": flag,
            "flag_value": flag_value,
        }

    def _classify_intent(self, text: str) -> str:
        text_lower = text.lower()
        scores: dict[str, float] = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower) / len(keywords)
            scores[intent] = score
        if not scores or max(scores.values()) == 0:
            return "general"
        return max(scores, key=scores.get)  # type: ignore

    def _extract_modifiers(self, text: str) -> dict[str, Any]:
        modifiers: dict[str, Any] = {}
        for pattern, key in self.METADATA_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                if key == "flag_value":
                    modifiers["flags"] = {m[0]: m[1] for m in matches}
                elif key == "flag":
                    modifiers["flags"] = modifiers.get("flags", {})
                    for m in matches:
                        modifiers["flags"][m] = True
                elif key == "level":
                    modifiers["level"] = int(matches[0]) if matches else 2
                elif key == "inline_modifier":
                    modifiers["inline"] = matches[0]
        return modifiers

    def _get_suggested_actions(self, intent: str, modifiers: dict[str, Any]) -> list[str]:
        suggestions: list[str] = []
        if intent == "code_generation":
            suggestions.append("Generate code with Coder agent")
            suggestions.append("Apply KB constraints")
        elif intent == "explanation":
            suggestions.append("Query knowledge base")
            suggestions.append("Retrieve relevant docs")
        elif intent == "listing":
            suggestions.append("List via ContextParser")
            suggestions.append("Search KB entries")
        elif intent == "modification":
            suggestions.append("Diff current vs proposed")
            suggestions.append("Apply with constraints")
        elif intent == "deletion":
            suggestions.append("Confirm before executing")
            suggestions.append("Backup state")
        elif intent == "execution":
            suggestions.append("Execute via MCP bridge")
            suggestions.append("Log command output")
        return suggestions

    def _calculate_confidence(self, text: str, intent: str, is_vibal: bool) -> float:
        base = 0.5
        if is_vibal:
            base += 0.3
        if len(text.split()) > 5:
            base += 0.1
        if any(c in text for c in [".", "!", "?"]):
            base += 0.05
        return min(base, 1.0)

    def format_suggestion(self, analysis: dict[str, Any]) -> str:
        intent = analysis["intent"]
        confidence = analysis["confidence"]
        modifier_summary = ", ".join(
            f"{k}={v}" for k, v in (analysis.get("modifiers") or {}).items()
        ) if analysis.get("modifiers") else "none"
        return (
            f"**VibeSense Analysis**\n"
            f"- Intent: `{intent}` ({confidence:.0%} confidence)\n"
            f"- Vibal: {analysis['is_vibal_command']}\n"
            f"- Modifiers: {modifier_summary}\n"
            f"- Suggested: {', '.join(analysis['suggested_actions'][:2])}"
        )
