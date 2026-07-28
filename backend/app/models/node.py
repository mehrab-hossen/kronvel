"""
Backend-facing node model.
Currently re-exports the shared contract — no backend-only fields needed yet.
Extend this (not shared/schemas/node.py) if backend-only persistence fields
are needed later, so the cross-service contract stays clean.
"""
from shared.schemas.node import GPUMetric, NodeHealthStatus, NodeState

__all__ = ["GPUMetric", "NodeHealthStatus", "NodeState"]
