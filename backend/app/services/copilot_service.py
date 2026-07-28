"""
Orchestrates Copilot chat sessions: maintains conversation history in Redis
hot state, and relays the CopilotAgent's event stream for the SSE route.
"""
import logging
from typing import AsyncIterator

from app.agents.copilot import AgentEvent, CopilotAgent
from app.models.copilot_session import ChatSession
from app.repositories.redis_repository import RedisRepository

logger = logging.getLogger("kronvel.services.copilot")

MAX_HISTORY_MESSAGES = 20  # bounded session length; long-term memory is out of MVP scope


class CopilotService:
    def __init__(self, agent: CopilotAgent, session_repo: RedisRepository[ChatSession]):
        self._agent = agent
        self._session_repo = session_repo

    async def stream_chat(self, session_id: str, user_message: str) -> AsyncIterator[AgentEvent]:
        session = await self._session_repo.get(session_id)
        if session is None:
            session = ChatSession(session_id=session_id, messages=[])

        history = session.messages[-MAX_HISTORY_MESSAGES:]

        final_answer: str | None = None
        async for event in self._agent.run(user_message, history=history):
            if event.type == "answer":
                final_answer = event.payload.get("text")
            yield event

        if final_answer is not None:
            session.messages.append({"role": "user", "content": user_message})
            session.messages.append({"role": "assistant", "content": final_answer})
            await self._session_repo.save(session_id, session)

        