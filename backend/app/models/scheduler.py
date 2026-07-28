"""Backend-facing scheduler model. Re-exports the shared contract — see node.py note."""
from shared.schemas.scheduler import NodeScore

__all__ = ["NodeScore"]