from app.models.session import Session, SessionCreate, SessionUpdateConstraints
from app.models.message import Message, MessageCreate, MessageRole
from app.utils.json_storage import get_storage
from datetime import datetime


class SessionManager:
    def __init__(self):
        self.storage = get_storage()

    async def create(self, data: SessionCreate | None = None) -> Session:
        session = Session()
        if data:
            if data.working_directory:
                session.context.working_directory = data.working_directory
            if data.language:
                session.context.language = data.language
        await self.storage.write("sessions", session.id, session.to_dict())
        return session

    async def get(self, session_id: str) -> Session | None:
        data = await self.storage.read("sessions", session_id)
        if data is None:
            return None
        return Session(**data)

    async def delete(self, session_id: str) -> bool:
        return await self.storage.delete("sessions", session_id)

    async def list_sessions(self) -> list[Session]:
        keys = await self.storage.list_keys("sessions")
        sessions = []
        for key in keys:
            data = await self.storage.read("sessions", key)
            if data:
                sessions.append(Session(**data))
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    async def add_message(
        self, session_id: str, message: MessageCreate
    ) -> Message | None:
        session = await self.get(session_id)
        if session is None:
            return None
        msg = Message(
            role=message.role,
            content=message.content,
            metadata={"tokens_used": 0, "model": "", "attachments": message.attachments},
        )
        session.messages.append(msg.to_dict())
        session.updated_at = datetime.utcnow()
        await self.storage.write("sessions", session.id, session.to_dict())
        return msg

    async def get_messages(self, session_id: str) -> list[Message] | None:
        session = await self.get(session_id)
        if session is None:
            return None
        return [Message(**m) for m in session.messages]

    async def update_state(self, session_id: str, **kwargs) -> Session | None:
        session = await self.get(session_id)
        if session is None:
            return None
        for key, value in kwargs.items():
            if hasattr(session.state, key):
                setattr(session.state, key, value)
        session.updated_at = datetime.utcnow()
        await self.storage.write("sessions", session.id, session.to_dict())
        return session

    async def add_artifact(self, session_id: str, artifact: dict) -> Session | None:
        session = await self.get(session_id)
        if session is None:
            return None
        session.artifacts.append(artifact)
        session.updated_at = datetime.utcnow()
        await self.storage.write("sessions", session.id, session.to_dict())
        return session

    async def update_constraints(
        self, session_id: str, data: SessionUpdateConstraints
    ) -> Session | None:
        session = await self.get(session_id)
        if session is None:
            return None

        if data.active is not None:
            session.constraints.active = data.active

        for rule_id in data.add_rules:
            if rule_id not in session.constraints.rules:
                session.constraints.rules.append(rule_id)
        for rule_id in data.remove_rules:
            if rule_id in session.constraints.rules:
                session.constraints.rules.remove(rule_id)

        for kb_id in data.add_knowledge_refs:
            if kb_id not in session.constraints.knowledge_refs:
                session.constraints.knowledge_refs.append(kb_id)
        for kb_id in data.remove_knowledge_refs:
            if kb_id in session.constraints.knowledge_refs:
                session.constraints.knowledge_refs.remove(kb_id)

        session.updated_at = datetime.utcnow()
        await self.storage.write("sessions", session.id, session.to_dict())
        return session
