"""
Reshapes raw Prometheus query results (Task 1's collector output) into typed
GPUMetric objects. This is the single seam between "Prometheus's data shape"
and "Kronvel's domain shape" — nothing downstream should ever see raw PromQL results.
"""

import logging
from zoneinfo import ZoneInfo
from datetime import datetime, timezone

from shared.schemas.node import GPUMetric

logger = logging.getLogger("kronvel.pipeline.processor")

_METRIC_FIELD_MAP = {
    "DCGM_FI_DEV_GPU_TEMP": "temperature_celsius",
    "DCGM_FI_DEV_GPU_UTIL": "utilization_percent",
    "DCGM_FI_DEV_FB_USED": "memory_used_mib",
    "DCGM_FI_DEV_POWER_USAGE": "power_watts",
    "DCGM_FI_DEV_XID_ERRORS": "xid_error_code",
    "DCGM_FI_DEV_ECC_SBE_VOL_TOTAL": "ecc_sbe_total",
}


def raw_to_gpu_metrics(raw: dict[str, list[dict]]) -> list[GPUMetric]:
    accumulated: dict[tuple[str, str], dict] = {}

    for metric_name, series_list in raw.items():
        field = _METRIC_FIELD_MAP.get(metric_name)
        if field is None:
            continue

        for series in series_list:
            labels = series.get("metric", {})
            node = labels.get("node")
            gpu = labels.get("gpu")

            if not node or gpu is None:
                continue

            key = (node, gpu)

            try:
                timestamp = datetime.fromtimestamp(
                    float(series["value"][0]),
                    tz=timezone.utc,
                    # tz=ZoneInfo("Asia/Dhaka"),
                )
                value = float(series["value"][1])
            except (KeyError, IndexError, TypeError, ValueError):
                logger.warning(
                    "Malformed series for %s on %s/%s, skipping",
                    metric_name,
                    node,
                    gpu,
                )
                continue

            gpu_fields = accumulated.setdefault(key, {})
            gpu_fields[field] = value
            gpu_fields.setdefault("observed_at", timestamp)

    metrics: list[GPUMetric] = []

    required = {
        "temperature_celsius",
        "utilization_percent",
        "memory_used_mib",
        "power_watts",
    }

    for (node, gpu), fields in accumulated.items():
        if not required.issubset(fields):
            logger.warning(
                "Dropping %s/%s. Fields received: %s",
                node,
                gpu,
                list(fields.keys()),
            )
            logger.warning(
                "Incomplete metric set for %s/%s, skipping this cycle",
                node,
                gpu,
            )
            continue

        metrics.append(
            GPUMetric(
                node=node,
                gpu_index=gpu,
                temperature_celsius=fields["temperature_celsius"],
                utilization_percent=fields["utilization_percent"],
                memory_used_mib=fields["memory_used_mib"],
                power_watts=fields["power_watts"],
                xid_error_code=int(fields.get("xid_error_code", 0)),
                ecc_sbe_total=int(fields.get("ecc_sbe_total", 0)),
                observed_at=fields["observed_at"],
            )
        )
    # logger.warning("PROCESSED GPU METRICS: %s", metrics)
    return metrics
