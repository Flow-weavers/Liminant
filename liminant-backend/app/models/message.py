from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"


class Message(BaseModel):
    id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    role: MessageRole = MessageRole.USER
    content: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=lambda: {
        "tokens_used": 0,
        "model": "",
        "attachments": [],
    })

    def to_dict(self) -> dict:
        data = self.model_dump(mode="json")
        data["timestamp"] = self.timestamp.isoformat()
        return data


class MessageCreate(BaseModel):
    content: str
    role: MessageRole = MessageRole.USER
    attachments: list[str] = Field(default_factory=list)
