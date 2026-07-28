"""
Agent tool: ad-hoc Prometheus queries for Copilot investigation.

Read-only by construction — Prometheus's /api/v1/query endpoint has no write
capability, so this tool requires no additional safety gating (contrast with
kubectl.py, which is the tool that does need explicit allowlisting per
SECURITY.md).
"""
import httpx

from app.core.config import get_settings


class PrometheusTool:
    name = "query_prometheus"
    description = "Run a PromQL query against live cluster metrics and return current values."

    def __init__(self, base_url: str | None = None):
        settings = get_settings()
        self._base_url = base_url or settings.prometheus_url

    async def run(self, promql_query: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self._base_url}/api/v1/query", params={"query": promql_query})
            response.raise_for_status()
            payload = response.json()
            if payload.get("status") != "success":
                raise RuntimeError(f"Prometheus query failed: {payload}")
            return [
                {"labels": result["metric"], "value": result["value"][1]}
                for result in payload["data"]["result"]
            ]
        