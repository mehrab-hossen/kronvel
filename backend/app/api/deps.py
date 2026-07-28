from typing import AsyncIterator

import asyncpg
import redis.asyncio as aioredis
from fastapi import Request

from app.repositories.postgres_repository import (
    PostgresAnomalyRepository,
    PostgresNodeRepository,
)
from app.services.anomaly_service import AnomalyService
from app.services.copilot_service import CopilotService

from app.services.remediation_service import RemediationService

from app.services.scheduler_service import SchedulerService


def get_redis_client(request: Request) -> aioredis.Redis:
    return request.app.state.redis_client


def get_pg_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pg_pool


def get_node_repository(request: Request) -> PostgresNodeRepository:
    return PostgresNodeRepository(request.app.state.pg_pool)


def get_anomaly_repository(request: Request) -> PostgresAnomalyRepository:
    return PostgresAnomalyRepository(request.app.state.pg_pool)


def get_anomaly_service(request: Request) -> AnomalyService:
    return request.app.state.anomaly_service


def get_copilot_service(request: Request) -> CopilotService:
    return request.app.state.copilot_service


def get_remediation_service(request: Request) -> RemediationService:
    return request.app.state.remediation_service


def get_scheduler_service(request: Request) -> SchedulerService:
    return request.app.state.scheduler_service

