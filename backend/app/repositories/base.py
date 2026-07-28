from typing import Any, Generic, Protocol, TypeVar

T = TypeVar("T")


class Repository(Protocol, Generic[T]):
    """
    Storage-agnostic repository contract.
    Concrete implementations: RedisRepository (hot state), PostgresRepository (durable state).
    Services depend on this Protocol, never on a concrete implementation.
    """

    async def get(self, key: str) -> T | None:
        ...

    async def save(self, key: str, item: T) -> None:
        ...

    async def list(self, **filters: Any) -> list[T]:
        ...

    async def delete(self, key: str) -> None:
        ...


        