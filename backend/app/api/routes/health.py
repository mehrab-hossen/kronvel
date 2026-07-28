from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> JSONResponse:
    checks: dict[str, str] = {}
    healthy = True

    try:
        await request.app.state.redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"
        healthy = False

    try:
        async with request.app.state.pg_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        checks["postgres"] = "ok"
    except Exception as exc:
        checks["postgres"] = f"error: {exc}"
        healthy = False

    status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content={"status": "ok" if healthy else "degraded", "checks": checks})
