import re
from typing import Any
from app.agents.librarian import LibrarianAgent


INTENT_PATTERNS = [
    (r"^(新建|创建|写|生成|make|new|create|write)\s+(一个?\s+)?(文件|file|代码|code|函数|function|组件|component)", "file_creation"),
    (r"^(修改|编辑|更新|改动|改变|edit|update|modify|change|refactor)", "modification"),
    (r"^(删除|移除|去掉|remove|delete)", "deletion"),
    (r"^(解释|说明|讲|explain|describe|what is)", "explanation"),
    (r"^(总结|summarize|概述|overview)", "summarization"),
    (r"^(搜索|查找|找|search|find|lookup)", "search"),
    (r"^(执行|运行|运行|run|execute|start)", "execution"),
    (r"^\.", "vibal_command"),
    (r"^(帮我|请|I want|I need|can you|could you)", "request"),
]


class PreflightService:
    def __init__(self):
        self.librarian = LibrarianAgent()
        self._intent_patterns = [(re.compile(p, re.I), i) for p, i in INTENT_PATTERNS]

    def _classify_intent(self, text: str) -> str:
        for pattern, intent in self._intent_patterns:
            if pattern.search(text):
                return intent
        return "general"

    def _extract_requirements(self, text: str) -> list[str]:
        reqs = []
        text_lower = text.lower()

        if any(w in text_lower for w in ["新建", "create", "new", "写"]):
            reqs.append("file creation requested")
        if any(w in text_lower for w in ["with", "using", "采用", "基于"]):
            reqs.append("specific implementation approach")
        if any(w in text_lower for w in ["test", "测试", "spec"]):
            reqs.append("testing expected")
        if any(w in text_lower for w in ["read", "读", "查看", "check"]):
            reqs.append("read operation")
        if any(w in text_lower for w in ["error", "bug", "错误", "修复", "fix"]):
            reqs.append("error fixing")

        return reqs

    def _find_context_anchors(self, session: dict[str, Any]) -> list[dict[str, str]]:
        anchors = []
        artifacts = session.get("artifacts", [])
        for a in artifacts[-3:]:
            anchors.append({
                "id": a.get("id", ""),
                "path": a.get("path", ""),
                "type": a.get("type", "file"),
                "label": f"{a.get('type', 'file')}: {a.get('path', 'unknown')}",
            })

        messages = session.get("messages", [])
        user_msgs = [m for m in messages if m.get("role") == "user"][-2:]
        for m in user_msgs:
            content = m.get("content", "")[:80]
            anchors.append({
                "id": m.get("id", ""),
                "path": "",
                "type": "message",
                "label": f"user: {content}...",
            })

        return anchors

    async def analyze(self, user_input: str, session: dict[str, Any]) -> dict[str, Any]:
        intent = self._classify_intent(user_input)
        requirements = self._extract_requirements(user_input)
        anchors = self._find_context_anchors(session)

        kb_results = await self.librarian.run({
            "query": user_input,
            "session": session,
            "limit": 5,
        })

        kb_entries = []
        for e in kb_results.get("results", []):
            kb_entries.append({
                "id": e.get("id", ""),
                "title": e.get("title", ""),
                "type": e.get("type", "rule"),
                "content_preview": e.get("content", "")[:120],
                "relevance_score": e.get("relevance_score", 0),
            })

        return {
            "intent": intent,
            "intent_label": self._intent_label(intent),
            "requirements": requirements,
            "kb_entries": kb_entries,
            "anchors": anchors,
            "confidence": self._compute_confidence(kb_entries, requirements),
        }

    def _intent_label(self, intent: str) -> str:
        labels = {
            "file_creation": "Create / Write File",
            "modification": "Modify / Refactor",
            "deletion": "Delete / Remove",
            "explanation": "Explain / Understand",
            "summarization": "Summarize",
            "search": "Search / Lookup",
            "execution": "Execute / Run",
            "vibal_command": "Vibal Command",
            "request": "General Request",
            "general": "General",
        }
        return labels.get(intent, intent)

    def _compute_confidence(self, kb_entries: list[dict], requirements: list[str]) -> float:
        score = 0.5
        if kb_entries:
            top_score = max(e.get("relevance_score", 0) for e in kb_entries)
            score = max(0.5, min(0.95, 0.5 + top_score * 0.3))
        if requirements:
            score = min(0.95, score + 0.1)
        return round(score, 2)
