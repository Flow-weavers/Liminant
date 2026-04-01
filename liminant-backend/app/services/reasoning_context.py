from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PipelinePhase(str, Enum):
    ABSORBING = "absorbing"
    CONSTRAINING = "constraining"
    GENERATING = "generating"
    VALIDATING = "validating"
    DONE = "done"


@dataclass
class ReasoningContext:
    user_input: str = ""
    session_id: str = ""
    working_directory: str = "/workspace/default"
    language: str = "en-US"
    response_text: str = ""
    intent: str = "general"
    requirements: list[str] = field(default_factory=list)
    kb_entries: list[dict] = field(default_factory=list)
    applied_constraints: list[dict] = field(default_factory=list)
    optimization_notes: list[str] = field(default_factory=list)
    pipeline_stage: int = 0
    phase: PipelinePhase = PipelinePhase.ABSORBING
    is_vibal_command: bool = False
    vibal_response: str = ""
    generated_code: str = ""
    generated_path: str = ""
    tools_used: list[dict] = field(default_factory=list)
    artifacts: list[dict] = field(default_factory=list)
    error: str = ""
    pipeline_complete: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_input": self.user_input,
            "session_id": self.session_id,
            "intent": self.intent,
            "requirements": self.requirements,
            "kb_entries": [self._entry_summary(e) for e in self.kb_entries],
            "applied_constraints": [self._entry_summary(e) for e in self.applied_constraints],
            "optimization_notes": self.optimization_notes,
            "pipeline_stage": self.pipeline_stage,
            "phase": self.phase.value,
            "is_vibal_command": self.is_vibal_command,
            "pipeline_complete": self.pipeline_complete,
            "tools_used": [
                {"name": t.get("name", ""), "args": t.get("args", {}), "result": t.get("result", {}).get("success")}
                for t in self.tools_used
            ],
            "artifacts": self.artifacts,
            "error": self.error,
        }

    @staticmethod
    def _entry_summary(e: dict) -> dict:
        return {
            "id": e.get("id", ""),
            "type": e.get("type", "rule"),
            "title": e.get("content", {}).get("title", "Untitled"),
            "body": e.get("content", {}).get("body", "")[:120],
        }
