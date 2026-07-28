"""Backend-facing anomaly model. Re-exports the shared contract — see node.py note."""
from shared.schemas.anomaly import Anomaly, AnomalySeverity, AnomalyType

__all__ = ["Anomaly", "AnomalySeverity", "AnomalyType"]

