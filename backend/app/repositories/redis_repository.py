from typing import Any, Generic, Type, TypeVar

import redis.asyncio as aioredis
from pydantic import BaseModel, ValidationError

from app.core.exceptions import RepositoryError

T = TypeVar("T", bound=BaseModel)


class RedisRepository(Generic[T]):
    """
    Generic JSON-serializing repository backed by Redis.
    Used for hot state: live node status, in-flight remediation actions (Day 6+).
    """

    def __init__(self, client: aioredis.Redis, model: Type[T], namespace: str):
        self._client = client
        self._model = model
        self._namespace = namespace

    def _full_key(self, key: str) -> str:
        return f"{self._namespace}:{key}"

    async def get(self, key: str) -> T | None:
        raw = await self._client.get(self._full_key(key))
        if raw is None:
            return None

        try:
            return self._model.model_validate_json(raw)
        except ValidationError as exc:
            raise RepositoryError(f"Corrupt value at key '{key}': {exc}") from exc

    async def save(self, key: str, item: T) -> None:
        await self._client.set(self._full_key(key), item.model_dump_json())

    async def list(self, **filters: Any) -> list[T]:
        # Filters are not indexed in Redis — list() scans the namespace.
        # Acceptable for MVP scale; a Postgres repository is used wherever
        # real querying is required (see postgres_repository.py).
        pattern = f"{self._namespace}:*"
        items: list[T] = []

        async for raw_key in self._client.scan_iter(match=pattern):
            raw = await self._client.get(raw_key)
            if raw is None:
                continue

            try:
                items.append(self._model.model_validate_json(raw))
            except ValidationError as exc:
                key = (
                    raw_key.decode("utf-8")
                    if isinstance(raw_key, bytes)
                    else str(raw_key)
                )
                raise RepositoryError(
                    f"Corrupt value at key '{key}': {exc}"
                ) from exc

        return items

    async def delete(self, key: str) -> None:
        await self._client.delete(self._full_key(key))

        