"""
Shared contract for scheduler/placement scoring output.

Consumed by:
- backend/ml/scheduler (produces)
- frontend (renders)
"""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


Reason = Annotated[str, Field(min_length=1)]


class NodeScore(BaseModel):
    """Placement score assigned to a candidate node by the scheduler."""

    model_config = ConfigDict(extra="forbid")

    node: str = Field(
        ...,
        min_length=1,
        description="Node identifier, e.g. 'gpu-node-1'",
    )
    score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Placement score (higher = better placement candidate)",
    )
    reasons: list[Reason] = Field(
        default_factory=list,
        description="Human-readable factors contributing to the score",
    )
    computed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the placement score was computed (UTC)",
    )

