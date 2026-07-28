"""
Shared contract for GPU node and per-GPU telemetry.

Consumed by:
- simulator (emits)
- backend/pipeline (collects)
- backend/models (persists)
"""

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NodeHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class GPUMetric(BaseModel):
    """Single-GPU telemetry snapshot, matching DCGM-style exposition fields."""

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
    temperature_celsius: float = Field(
        ...,
        ge=0,
        le=150,
        description="GPU temperature in Celsius",
    )
    utilization_percent: float = Field(
        ...,
        ge=0,
        le=100,
        description="GPU utilization percentage",
    )
    memory_used_mib: float = Field(
        ...,
        ge=0,
        description="GPU memory used (MiB)",
    )
    power_watts: float = Field(
        ...,
        ge=0,
        description="GPU power draw (Watts)",
    )
    xid_error_code: int = Field(
        0,
        description="0 = no active XID error",
    )
    ecc_sbe_total: int = Field(
        0,
        ge=0,
        description="Cumulative single-bit ECC errors",
    )
    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the telemetry was observed (UTC)",
    )


class NodeState(BaseModel):
    """Aggregated node-level state derived from one or more GPUMetric snapshots."""

    model_config = ConfigDict(extra="forbid")

    node: str = Field(
        ...,
        min_length=1,
        description="Node identifier",
    )
    gpu_count: int = Field(
        ...,
        ge=1,
        description="Total number of GPUs on the node",
    )
    health_status: NodeHealthStatus = Field(
        default=NodeHealthStatus.UNKNOWN,
        description="Overall node health status",
    )
    recovery_score: int = Field(
    default=100,
    ge=0,
    le=100,
    description="Gradual recovery confidence score (0-100).",
    )

    cordoned: bool = Field(
    default=False,
    description="Whether the Kubernetes node is cordoned (SchedulingDisabled).",
    )

    gpus: list[GPUMetric] = Field(
        default_factory=list,
        description="Telemetry snapshots for each GPU",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the node state was last updated (UTC)",
    )

    @model_validator(mode="after")
    def validate_gpu_count(self) -> "NodeState":
        if self.gpus and self.gpu_count != len(self.gpus):
            raise ValueError(
                f"gpu_count ({self.gpu_count}) must equal the number of GPU metrics ({len(self.gpus)})."
            )
        return self
    
    