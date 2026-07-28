"""
Drives the periodic collect -> detect -> persist cycle via APScheduler.

Single-replica by design: this scheduler runs in-process and does not
coordinate across multiple backend instances. Scaling the backend beyond
1 Railway replica while this worker is in-process would duplicate every
collection cycle. See docs/ARCHITECTURE.md 'Known Constraints' — the
production migration path is a queue-based worker (Celery/Redis) or a
Kubernetes CronJob, tracked in docs/ROADMAP.md Phase 2, not solved here.
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.anomaly_service import AnomalyService

logger = logging.getLogger("kronvel.pipeline.worker")


class CollectionWorker:
    def __init__(self, anomaly_service: AnomalyService, interval_seconds: int = 5):
        self._service = anomaly_service
        self._interval_seconds = interval_seconds
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        self._scheduler.add_job(
            self._tick,
            trigger="interval",
            seconds=self._interval_seconds,
            id="collection_cycle",
            max_instances=1,
            coalesce=True,
        )
        self._scheduler.start()
        logger.info("Collection worker started, interval=%ds", self._interval_seconds)

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("Collection worker stopped")

    async def _tick(self) -> None:
        try:
            await self._service.run_collection_cycle()
        except Exception:
            logger.exception("Collection cycle failed — will retry next interval")