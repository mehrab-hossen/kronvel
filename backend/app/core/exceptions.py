class KronvelError(Exception):
    """Base exception for all Kronvel domain errors."""


class RepositoryError(KronvelError):
    """Raised when a repository operation fails (connection, serialization, etc.)."""


class NotFoundError(KronvelError):
    """Raised when a requested entity does not exist."""


class PolicyViolationError(KronvelError):
    """Raised when a proposed action is blocked by the policy gate. Used starting Day 5-6."""


class ActionBlockedError(KronvelError):
    """Raised when remediation is attempted but not cleared for execution. Used starting Day 6."""

    