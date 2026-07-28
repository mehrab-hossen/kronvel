"""
Prometheus collection client.

This is the ONLY module that speaks Prometheus's query API — everything downstream
(processor, detector, service) works with typed domain objects, not raw PromQL results.
"""

import asyncio

import httpx

from app.core.config import get_settings

METRIC_NAMES = [
    "DCGM_FI_DEV_GPU_TEMP",
    "DCGM_FI_DEV_GPU_UTIL",
    "DCGM_FI_DEV_FB_USED",
    "DCGM_FI_DEV_POWER_USAGE",
    "DCGM_FI_DEV_XID_ERRORS",
    "DCGM_FI_DEV_ECC_SBE_VOL_TOTAL",
]


class PrometheusCollector:
    def __init__(self, base_url: str | None = None):
        settings = get_settings()
        self._base_url = base_url or settings.prometheus_url

    async def _instant_query(
        self,
        client: httpx.AsyncClient,
        query: str,
    ) -> list[dict]:
        response = await client.get(
            f"{self._base_url}/api/v1/query",
            params={"query": query},
        )
        response.raise_for_status()

        payload = response.json()
        if payload.get("status") != "success":
            raise RuntimeError(
                f"Prometheus query failed for '{query}': {payload}"
            )

        return payload["data"]["result"]

    async def collect_raw(self) -> dict[str, list[dict]]:
        """
        Returns:
            {
                metric_name: [Prometheus result series, ...],
                ...
            }
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            metric_names = list(METRIC_NAMES)

            responses = await asyncio.gather(
                *(
                    self._instant_query(client, metric_name)
                    for metric_name in metric_names
                )
            )

            return dict(zip(metric_names, responses, strict=True))
        
