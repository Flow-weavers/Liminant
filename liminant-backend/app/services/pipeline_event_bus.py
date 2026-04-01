import asyncio
from typing import Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class PipelineStageEvent:
    session_id: str
    phase: str
    stage: int
    data: dict[str, Any]
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PipelineEventBus:
    _instance: "PipelineEventBus | None" = None

    def __init__(self):
        self._subscribers: dict[str, list[Callable[[PipelineStageEvent], None]]] = {}
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "PipelineEventBus":
        if cls._instance is None:
            cls._instance = PipelineEventBus()
        return cls._instance

    def subscribe(self, session_id: str, callback: Callable[[PipelineStageEvent], None]) -> None:
        if session_id not in self._subscribers:
            self._subscribers[session_id] = []
        self._subscribers[session_id].append(callback)

    def unsubscribe(self, session_id: str, callback: Callable[[PipelineStageEvent], None]) -> None:
        if session_id in self._subscribers:
            self._subscribers[session_id] = [
                cb for cb in self._subscribers[session_id] if cb != callback
            ]

    async def publish(self, event: PipelineStageEvent) -> None:
        callbacks: list[Callable] = []
        async with self._lock:
            callbacks = list(self._subscribers.get(event.session_id, []))

        for cb in callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(event)
                else:
                    cb(event)
            except Exception:
                pass

    def emit(self, session_id: str, phase: str, stage: int, data: dict[str, Any]) -> None:
        event = PipelineStageEvent(
            session_id=session_id,
            phase=phase,
            stage=stage,
            data=data,
            timestamp=datetime.utcnow().isoformat(),
        )
        asyncio.create_task(self.publish(event))

    def broadcast_tool_result(
        self, session_id: str, tool_name: str, args: dict, result: dict
    ) -> None:
        self.emit(session_id, "tool_result", 3, {
            "tool_name": tool_name,
            "args": args,
            "result": result,
        })
