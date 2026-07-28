import os
from datetime import datetime, timezone

import pytest

from app.repositories.postgres_repository import (
    PostgresAnomalyRepository,
    init_pool,
)
from shared.schemas.anomaly import (
    Anomaly,
    AnomalySeverity,
    AnomalyType,
)


@pytest.mark.asyncio
async def test_postgres_anomaly_repository_save_and_list():
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://kronvel:kronvel@localhost:5432/kronvel"
    )

    pool = await init_pool(database_url)
    repo = PostgresAnomalyRepository(pool)

    anomaly = Anomaly(
        node="test-node",
        gpu_index="0",
        anomaly_type=AnomalyType.THERMAL,
        severity=AnomalySeverity.HIGH,
        metric_value=95.0,
        threshold=85.0,
        description="unit test anomaly",
        detected_at=datetime.now(timezone.utc),
    )

    await repo.save("unused", anomaly)

    results = await repo.list(node="test-node")

    assert len(results) >= 1
    assert results[0].node == "test-node"

    await pool.close()

