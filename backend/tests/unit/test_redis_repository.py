import os

import pytest
import redis.asyncio as aioredis
from pydantic import BaseModel

from app.repositories.redis_repository import RedisRepository


class DummyModel(BaseModel):
    name: str
    value: int


@pytest.mark.asyncio
async def test_redis_repository_save_get_delete():
    redis_url = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0"
    )

    client = aioredis.from_url(redis_url)

    repo = RedisRepository(
        client,
        DummyModel,
        namespace="test_unit"
    )

    await repo.save("k1", DummyModel(name="node-1", value=1))

    result = await repo.get("k1")

    assert result is not None
    assert result.name == "node-1"

    await repo.delete("k1")

    assert await repo.get("k1") is None

    await client.aclose()

