"""
Shared contract for detected anomalies.

Consumed by:
- backend/ml/anomaly (produces)
- backend/models (persists)
- frontend (renders)
"""

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AnomalyType(str, Enum):
    THERMAL = "thermal"
    XID_ERROR = "xid_error"
    ECC_ERROR = "ecc_error"
    UTILIZATION = "utilization"
    UNKNOWN = "unknown"


class AnomalySeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Anomaly(BaseModel):
    """Represents an anomaly detected for a specific GPU metric."""

    model_config = ConfigDict(extra="forbid")

    node: str = Field(
        ...,
        min_length=1,
        description="Node identifier, e.g. 'gpu-node-1'",
    )
    gpu_index: str = Field(
        ...,
        min_length=1,
        description="GPU identifier within the node, as reported by telemetry",
    )
    anomaly_type: AnomalyType = Field(
        ...,
        description="Type of detected anomaly",
    )
    severity: AnomalySeverity = Field(
        ...,
        description="Severity level of the anomaly",
    )
    metric_value: float = Field(
        ...,
        ge=0,
        description="Observed metric value that triggered the anomaly",
    )
    threshold: float = Field(
        ...,
        ge=0,
        description="Threshold value used for anomaly detection",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Human-readable explanation of the anomaly",
    )
    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the anomaly was detected (UTC)",
    )

