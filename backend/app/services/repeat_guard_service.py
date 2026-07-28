from collections import defaultdict
from datetime import datetime, timedelta, timezone


class RepeatGuard:
    """
    Prevents repeated remediation loops.

    Example:
    gpu-node-6 + cordon

    Attempt 1 -> allow
    Attempt 2 -> allow
    Attempt 3 -> allow
    Attempt 4 -> block
    """

    def __init__(
        self,
        max_attempts: int = 3,
        window_minutes: int = 30,
    ):
        self.max_attempts = max_attempts
        self.window = timedelta(minutes=window_minutes)

        self._events: dict[str, list[datetime]] = defaultdict(list)


    def check(
        self,
        node: str,
        action: str,
    ) -> dict:

        key = f"{node}:{action}"

        now = datetime.now(timezone.utc)

        # Remove expired attempts
        self._events[key] = [
            timestamp
            for timestamp in self._events[key]
            if now - timestamp < self.window
        ]

        attempts = len(self._events[key]) + 1

        allowed = attempts <= self.max_attempts

        if allowed:
            self._events[key].append(now)

        return {
            "allowed": allowed,
            "attempts": attempts,
            "limit": self.max_attempts,
        }
    