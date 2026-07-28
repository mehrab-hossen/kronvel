"""
Backend-only model — a chat session has no reason to exist in shared/schemas,
since neither the simulator nor any other service needs to know its shape.
"""
from pydantic import BaseModel, Field


class ChatSession(BaseModel):
    session_id: str
    messages: list[dict] = Field(default_factory=list)

    