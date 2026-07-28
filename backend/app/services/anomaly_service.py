"""
Orchestrates the collection -> detection -> persistence cycle, and serves
the read paths consumed by api/routes/anomaly.py.
"""

import logging

from app.core.exceptions import RepositoryError
from app.ml.anomaly.detector import AnomalyDetector
from app.pipeline.collector import PrometheusCollector
from app.pipeline.processor import raw_to_gpu_metrics
from app.repositories.postgres_repository import (
    PostgresAnomalyRepository,
    PostgresNodeRepository,
)
from app.repositories.redis_repository import RedisRepository
from shared.schemas.anomaly import (
    Anomaly,
    AnomalySeverity
)
from shared.schemas.node import GPUMetric, NodeHealthStatus, NodeState
from app.agents.tools.kubectl import KubectlTool
from app.services.remediation_service import RemediationService
from app.services.recovery_service import RecoveryScoreService


logger = logging.getLogger("kronvel.services.anomaly")


class AnomalyService:
    def __init__(
        self,
        collector: PrometheusCollector,
        detector: AnomalyDetector,
        anomaly_repo: PostgresAnomalyRepository,
        node_repo: PostgresNodeRepository,
        node_hot_state: RedisRepository[NodeState],
        # kubectl_tool: KubectlTool,
        remediation_service: RemediationService,
        recovery_service: RecoveryScoreService,


    ):
        self._collector = collector
        self._detector = detector
        self._anomaly_repo = anomaly_repo
        self._node_repo = node_repo
        self._node_hot_state = node_hot_state
        # self._kubectl_tool = kubectl_tool
        self._remediation_service = remediation_service
        self._recovery_service = recovery_service

    async def run_collection_cycle(self) -> list[Anomaly]:
        try:
            raw = await self._collector.collect_raw()
            metrics = raw_to_gpu_metrics(raw)
        except Exception:
            logger.exception(
                "Collection cycle failed during metric collection or processing"
            )
            return []

        detected: list[Anomaly] = []
        metrics_by_node: dict[str, list[GPUMetric]] = {}

        for metric in metrics:
            metrics_by_node.setdefault(metric.node, []).append(metric)

            anomaly = self._detector.evaluate(metric)
            if anomaly is None:
                continue

            detected.append(anomaly)

            try:
                await self._anomaly_repo.save("unused", anomaly)
            except RepositoryError:
                logger.exception(
                    "Failed to persist anomaly for node %s — continuing cycle",
                    anomaly.node,
                )

        for node, gpu_metrics in metrics_by_node.items():
            node_anomalies = [a for a in detected if a.node == node]

            if any(a.severity == AnomalySeverity.CRITICAL for a in node_anomalies):
                health = NodeHealthStatus.CRITICAL
            elif node_anomalies:
                health = NodeHealthStatus.DEGRADED
            else:
                health = NodeHealthStatus.HEALTHY

            recovery_score = self._recovery_service.update(
                node=node,
                healthy=health == NodeHealthStatus.HEALTHY,
            )


            is_cordoned = await self._node_repo.is_cordoned(node)
            node_state = NodeState(
                node=node,
                gpu_count=len(gpu_metrics),
                health_status=health,
                # cordoned=False,  # Temporary; we'll populate this from Kubernetes later.
                # cordoned=await self._kubectl_tool.is_cordoned(node),
                cordoned=is_cordoned,
                gpus=gpu_metrics,
                recovery_score=recovery_score,

            )

            if (
                is_cordoned
                and health == NodeHealthStatus.HEALTHY
                and max(g.temperature_celsius for g in gpu_metrics) < 65
            ):
                try:
                    audit = await self._remediation_service.execute(
                        action="uncordon",
                        node=node,
                        dry_run=False,
                        requested_by="auto-recovery",
                    )

                    if audit.executed:
                        node_state.cordoned = False

                    logger.info(
                        "Automatically uncordoned %s after recovery.",
                        node,
                    )

                except Exception:
                    logger.exception(
                        "Failed to auto-uncordon %s",
                        node,
                    )

            try:
                await self._node_hot_state.save(node, node_state)
                await self._node_repo.save(node, node_state)
            except RepositoryError:
                logger.exception(
                    "Failed to persist node state for %s — continuing cycle",
                    node,
                )

        if detected:
            logger.info(
                "Collection cycle complete: %d anomalies detected",
                len(detected),
            )

        return detected

    async def list_anomalies(self, node: str | None = None) -> list[Anomaly]:
        filters = {"node": node} if node else {}
        return await self._anomaly_repo.list(**filters)

    async def list_nodes(self) -> list[NodeState]:
        # Prefer hot state (Redis) — freshest, updated every cycle.
        # Fall back to durable state only if hot state is empty
        # (e.g. right after a restart).
        nodes = await self._node_hot_state.list()
        if nodes:
            return nodes

        return await self._node_repo.list()
    
    