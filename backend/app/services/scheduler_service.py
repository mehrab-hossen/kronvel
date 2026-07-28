from app.ml.scheduler.scorer import HeuristicScheduler
from app.services.anomaly_service import AnomalyService
from shared.schemas.scheduler import NodeScore


class SchedulerService:
    def __init__(self, anomaly_service: AnomalyService, scorer: HeuristicScheduler):
        self._anomaly_service = anomaly_service
        self._scorer = scorer

    async def get_scores(self) -> list[NodeScore]:
        nodes = await self._anomaly_service.list_nodes()
        return self._scorer.score(nodes)
    