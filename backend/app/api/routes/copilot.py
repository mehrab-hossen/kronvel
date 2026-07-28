import json
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.deps import get_copilot_service
from app.services.copilot_service import CopilotService

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


@router.post("/copilot/chat")
async def copilot_chat(request: ChatRequest, service: CopilotService = Depends(get_copilot_service)):
    session_id = request.session_id or str(uuid.uuid4())

    async def event_stream():
        yield f"event: session\ndata: {json.dumps({'session_id': session_id})}\n\n"
        async for event in service.stream_chat(session_id, request.message):
            yield f"event: {event.type}\ndata: {json.dumps(event.payload, default=str)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
