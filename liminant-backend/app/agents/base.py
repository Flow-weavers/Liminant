from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    def __init__(self, agent_id: str, agent_type: str):
        self.id = agent_id
        self.type = agent_type
        self.state: dict[str, Any] = {"status": "idle", "current_task": "", "progress": 0.0}

    @abstractmethod
    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        pass

    def set_state(self, status: str, task: str = "", progress: float = 0.0) -> None:
        self.state["status"] = status
        self.state["current_task"] = task
        self.state["progress"] = progress
