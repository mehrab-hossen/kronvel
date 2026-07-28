from fastapi import APIRouter, Depends

from app.api.deps import get_scheduler_service
from app.services.scheduler_service import SchedulerService
from shared.schemas.scheduler import NodeScore

router = APIRouter()


@router.get("/scheduler/score", response_model=list[NodeScore])
async def scheduler_score(service: SchedulerService = Depends(get_scheduler_service)) -> list[NodeScore]:
    return await service.get_scores()
