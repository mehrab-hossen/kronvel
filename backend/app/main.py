from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
from typing import AsyncIterator

import redis.asyncio as aioredis
from fastapi import FastAPI

from app.api.routes import anomaly, copilot, health, remediation, scheduler

import logging

from app.agents.copilot import CopilotAgent
from app.agents.policy import PolicyGate
from app.agents.provider import LLMProvider
from app.agents.tools.kubectl import KubectlTool
from app.agents.tools.node_state import NodeStateTool
from app.agents.tools.prometheus import PrometheusTool
from app.models.copilot_session import ChatSession
from app.services.copilot_service import CopilotService

logger = logging.getLogger("kronvel.main")

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.ml.anomaly.detector import AnomalyDetector
from app.ml.scheduler.scorer import HeuristicScheduler
from app.pipeline.collector import PrometheusCollector
from app.pipeline.worker import CollectionWorker
from app.repositories.postgres_repository import (
    PostgresActionAuditRepository,
    PostgresAnomalyRepository,
    PostgresNodeRepository,
    init_pool,
)
from app.repositories.redis_repository import RedisRepository
from app.services.anomaly_service import AnomalyService
from app.services.scheduler_service import SchedulerService
from app.services.remediation_service import RemediationService
from app.services.repeat_guard_service import RepeatGuard
from app.services.recovery_service import RecoveryScoreService
from shared.schemas.node import NodeState


settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    redis_client = None
    pg_pool = None
    worker = None

    try:
        redis_client = aioredis.from_url(settings.redis_url)
        pg_pool = await init_pool(settings.database_url)

        app.state.redis_client = redis_client
        app.state.pg_pool = pg_pool

        node_hot_state = RedisRepository(
            redis_client,
            NodeState,
            namespace="node_state",
        )

        anomaly_repo = PostgresAnomalyRepository(pg_pool)
        node_repo = PostgresNodeRepository(pg_pool)

        collector = PrometheusCollector()

        detector = AnomalyDetector(
            temp_z_threshold=settings.anomaly_temp_z_threshold,
            temp_absolute_threshold_c=settings.anomaly_temp_absolute_threshold_c,
            temp_critical_threshold_c=settings.anomaly_temp_critical_threshold_c,
        )

        try:
            kubectl_tool = KubectlTool(
                kubeconfig_path=settings.kube_config_path,
                in_cluster=settings.kube_in_cluster,
            )

            # await kubectl_tool.ensure_uncordoned()

        except Exception:
            logger.warning(
                "kubectl tool unavailable — no reachable cluster configured. "
                "Copilot will still answer read-only questions; kubectl_action is disabled."
            )
            kubectl_tool = None


        policy_gate = PolicyGate()

        repeat_guard = RepeatGuard(
            max_attempts=3,
            window_minutes=30,
        )
        recovery_service = RecoveryScoreService()

        audit_repo = PostgresActionAuditRepository(pg_pool)

        app.state.remediation_service = RemediationService(
            policy_gate=policy_gate,
            kubectl_tool=kubectl_tool,
            audit_repo=audit_repo,
            node_repo=node_repo,
            repeat_guard=repeat_guard,

        )

        app.state.recovery_service = recovery_service

        # # Ensure every demo starts with the Kubernetes node schedulable.
        # if kubectl_tool is not None:
        #     try:
        #         await kubectl_tool.run(
        #             action="uncordon",
        #             node="gpu-node-6",
        #             dry_run=False,
        #         )
        #         logger.info("Reset Kubernetes node to uncordoned state.")
        #     except Exception:
        #         logger.warning(
        #             "Could not reset Kubernetes node to uncordoned state."
        #         )

        anomaly_service = AnomalyService(
            collector=collector,
            detector=detector,
            anomaly_repo=anomaly_repo,
            node_repo=node_repo,
            node_hot_state=node_hot_state,
            # kubectl_tool=kubectl_tool,
            remediation_service=app.state.remediation_service,
            recovery_service=recovery_service,

        )

        app.state.anomaly_service = anomaly_service

        app.state.scheduler_service = SchedulerService(
            anomaly_service=app.state.anomaly_service,
            scorer=HeuristicScheduler(),
        )

        prometheus_tool = PrometheusTool()
        node_state_tool = NodeStateTool(fetch_nodes=app.state.anomaly_service.list_nodes)

        # try:
        #     kubectl_tool = KubectlTool(
        #         kubeconfig_path=settings.kube_config_path, in_cluster=settings.kube_in_cluster
        #     )
        # except Exception:
        #     logger.warning(
        #         "kubectl tool unavailable — no reachable cluster configured. "
        #         "Copilot will still answer read-only questions; kubectl_action is disabled."
        #     )
        #     kubectl_tool = None



        llm_provider = LLMProvider()

        copilot_agent = CopilotAgent(
            provider=llm_provider,
            prometheus_tool=prometheus_tool,
            node_state_tool=node_state_tool,
            kubectl_tool=kubectl_tool,
            policy_gate=policy_gate,
        )

        session_repo = RedisRepository(app.state.redis_client, ChatSession, namespace="copilot_session")
        app.state.copilot_service = CopilotService(agent=copilot_agent, session_repo=session_repo)

        worker = CollectionWorker(
            anomaly_service,
            interval_seconds=settings.pipeline_poll_interval_seconds,
        )
        worker.start()

        app.state.worker = worker

        yield

    finally:
        if worker is not None:
            worker.stop()

        if redis_client is not None:
            await redis_client.aclose()

        if pg_pool is not None:
            await pg_pool.close()


app = FastAPI(
    title="Kronvel Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(anomaly.router)
app.include_router(copilot.router)
app.include_router(remediation.router)
app.include_router(scheduler.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "kronvel-backend",
        "status": "ok",
    }

