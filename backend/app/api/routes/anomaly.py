from fastapi import APIRouter, Depends, Query

from app.api.deps import get_anomaly_service
from app.services.anomaly_service import AnomalyService
from shared.schemas.anomaly import Anomaly
from shared.schemas.node import NodeState

router = APIRouter()


@router.get("/anomalies", response_model=list[Anomaly])
async def list_anomalies(
    node: str | None = Query(default=None, description="Filter by node name"),
    service: AnomalyService = Depends(get_anomaly_service),
) -> list[Anomaly]:
    return await service.list_anomalies(node=node)


@router.get("/nodes", response_model=list[NodeState])
async def list_nodes(service: AnomalyService = Depends(get_anomaly_service)) -> list[NodeState]:
    return await service.list_nodes()