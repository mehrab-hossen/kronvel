from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import asyncpg

from app.core.exceptions import RepositoryError
from shared.schemas.anomaly import Anomaly, AnomalySeverity, AnomalyType
from shared.schemas.node import NodeHealthStatus, NodeState

import json

from app.models.action_audit import ActionAudit

class PostgresNodeRepository:
    """Durable node state. Implements the Repository interface (see base.py)."""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def get(self, key: str) -> NodeState | None:
        row = await self._pool.fetchrow(
            "SELECT node, gpu_count, health_status, updated_at FROM nodes WHERE node = $1",
            key,
        )
        if row is None:
            return None

        cordoned = await self.is_cordoned(row["node"])

        return NodeState(
            node=row["node"],
            gpu_count=row["gpu_count"],
            health_status=NodeHealthStatus(row["health_status"]),
            cordoned=cordoned,  # Temporary placeholder
            gpus=[],  # Per-GPU detail lives in hot state (Redis).
            updated_at=row["updated_at"],
        )

    async def save(self, key: str, item: NodeState) -> None:
        try:
            await self._pool.execute(
                """
                INSERT INTO nodes (node, gpu_count, health_status, updated_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (node) DO UPDATE
                SET gpu_count = EXCLUDED.gpu_count,
                    health_status = EXCLUDED.health_status,
                    updated_at = EXCLUDED.updated_at
                """,
                key,
                item.gpu_count,
                item.health_status.value,
                item.updated_at,
            )
        except asyncpg.PostgresError as exc:
            raise RepositoryError(f"Failed to save node '{key}': {exc}") from exc

    async def list(self, **filters: Any) -> list[NodeState]:
        rows = await self._pool.fetch(
            "SELECT node, gpu_count, health_status, updated_at FROM nodes"
        )

        nodes = []

        for row in rows:
            cordoned = await self.is_cordoned(row["node"])

            nodes.append(
                NodeState(
                    node=row["node"],
                    gpu_count=row["gpu_count"],
                    health_status=NodeHealthStatus(row["health_status"]),
                    cordoned=cordoned,
                    gpus=[],
                    updated_at=row["updated_at"],
                )
            )

        return nodes

    async def set_cordoned(
        self,
        node: str,
        cordoned: bool,
    ) -> None:
        try:
            await self._pool.execute(
                """
                INSERT INTO node_remediation_state
                    (node, cordoned)
                VALUES ($1, $2)

                ON CONFLICT (node)
                DO UPDATE
                SET
                    cordoned = EXCLUDED.cordoned,
                    updated_at = now()
                """,
                node,
                cordoned,
            )
        except asyncpg.PostgresError as exc:
            raise RepositoryError(
                f"Failed to update remediation state for '{node}': {exc}"
            ) from exc

    async def is_cordoned(
        self,
        node: str,
    ) -> bool:
        row = await self._pool.fetchrow(
            """
            SELECT cordoned
            FROM node_remediation_state
            WHERE node = $1
            """,
            node,
        )

        if row is None:
            return False

        return row["cordoned"]


    async def delete(self, key: str) -> None:
        await self._pool.execute(
            "DELETE FROM nodes WHERE node = $1",
            key,
        )


class PostgresAnomalyRepository:
    """Durable anomaly history. Implements the Repository interface (see base.py)."""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def get(self, key: str) -> Anomaly | None:
        row = await self._pool.fetchrow(
            "SELECT * FROM anomalies WHERE id = $1",
            int(key),
        )
        return self._row_to_model(row) if row else None

    async def save(self, key: str, item: Anomaly) -> None:
        # key is unused for inserts (id is SERIAL); present to satisfy the Repository interface.
        try:
            await self._pool.execute(
                """
                INSERT INTO anomalies (
                    node,
                    gpu_index,
                    anomaly_type,
                    severity,
                    metric_value,
                    threshold,
                    description,
                    detected_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                item.node,
                item.gpu_index,
                item.anomaly_type.value,
                item.severity.value,
                item.metric_value,
                item.threshold,
                item.description,
                item.detected_at,
            )
        except asyncpg.PostgresError as exc:
            raise RepositoryError(
                f"Failed to save anomaly for node '{item.node}': {exc}"
            ) from exc

    async def list(self, **filters: Any) -> list[Anomaly]:
        node = filters.get("node")

        if node:
            rows = await self._pool.fetch(
                """
                SELECT *
                FROM anomalies
                WHERE node = $1
                ORDER BY detected_at DESC
                LIMIT 100
                """,
                node,
            )
        else:
            rows = await self._pool.fetch(
                """
                SELECT *
                FROM anomalies
                ORDER BY detected_at DESC
                LIMIT 100
                """
            )

        return [self._row_to_model(row) for row in rows]

    async def delete(self, key: str) -> None:
        await self._pool.execute(
            "DELETE FROM anomalies WHERE id = $1",
            int(key),
        )

    @staticmethod
    def _row_to_model(row: asyncpg.Record) -> Anomaly:
        return Anomaly(
            node=row["node"],
            gpu_index=row["gpu_index"],
            anomaly_type=AnomalyType(row["anomaly_type"]),
            severity=AnomalySeverity(row["severity"]),
            metric_value=row["metric_value"],
            threshold=row["threshold"],
            description=row["description"],
            detected_at=row["detected_at"],
        )


class PostgresActionAuditRepository:
    """Durable audit trail — every proposed action, approved, blocked, or executed. Implements Repository."""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def get(self, key: str) -> ActionAudit | None:
        row = await self._pool.fetchrow("SELECT * FROM action_audit WHERE id = $1", key)
        return self._row_to_model(row) if row else None

    async def save(self, key: str, item: ActionAudit) -> None:
        try:
            await self._pool.execute(
                """
                INSERT INTO action_audit
                    (id, action, node, requested_by, dry_run, policy_decision, policy_risk_level,
                     policy_reason, executed, result, error, created_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
                ON CONFLICT (id) DO UPDATE SET
                    executed = EXCLUDED.executed,
                    result = EXCLUDED.result,
                    error = EXCLUDED.error
                """,
                key, item.action, item.node, item.requested_by, item.dry_run,
                item.policy_decision, item.policy_risk_level, item.policy_reason,
                item.executed, json.dumps(item.result) if item.result is not None else None,
                item.error, item.created_at,
            )
        except asyncpg.PostgresError as exc:
            raise RepositoryError(f"Failed to save action audit '{key}': {exc}") from exc

    async def list(self, **filters: Any) -> list[ActionAudit]:
        node = filters.get("node")
        if node:
            rows = await self._pool.fetch(
                "SELECT * FROM action_audit WHERE node = $1 ORDER BY created_at DESC LIMIT 100", node
            )
        else:
            rows = await self._pool.fetch("SELECT * FROM action_audit ORDER BY created_at DESC LIMIT 100")
        return [self._row_to_model(r) for r in rows]

    async def delete(self, key: str) -> None:
        await self._pool.execute("DELETE FROM action_audit WHERE id = $1", key)

    @staticmethod
    def _row_to_model(row: asyncpg.Record) -> ActionAudit:
        result = json.loads(row["result"]) if row["result"] else None
        return ActionAudit(
            id=row["id"], action=row["action"], node=row["node"], requested_by=row["requested_by"],
            dry_run=row["dry_run"], policy_decision=row["policy_decision"],
            policy_risk_level=row["policy_risk_level"], policy_reason=row["policy_reason"],
            executed=row["executed"], result=result, error=row["error"], created_at=row["created_at"],
        )


async def init_pool(dsn: str) -> asyncpg.Pool:
    pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=10)

    schema_path = Path(__file__).with_name("schema.sql")

    async with pool.acquire() as conn:
        await conn.execute(schema_path.read_text(encoding="utf-8"))

    return pool

