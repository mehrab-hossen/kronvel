"""
Rolling-window feature engineering for statistical anomaly detection.

Design note: state here is in-process (per-key deques), not persisted to Redis
or Postgres. This is acceptable because the collection worker (pipeline/worker.py)
is explicitly single-replica by design (see docs/ARCHITECTURE.md) — a restart
resets the baseline, which just means a brief re-warm-up period, not incorrect
behavior. This would need to move to a shared store if the worker is ever
horizontally scaled (tracked as post-MVP debt).

IMPORTANT:
For correct anomaly detection, callers MUST compute the Z-score before pushing
the current sample into the rolling window:

    score = window.z_score(key, value)
    window.push(key, value)

This ensures the current observation is evaluated against historical data only.
"""

import statistics
from collections import deque

WindowKey = tuple[str, str]  # (node, gpu_index)


class RollingWindow:
    def __init__(self, maxlen: int = 15, min_samples: int = 5):
        self._data: dict[WindowKey, deque[float]] = {}
        self._maxlen = maxlen
        self._min_samples = min_samples

    def push(self, key: WindowKey, value: float) -> None:
        """Append a new sample to the rolling history."""
        window = self._data.setdefault(key, deque(maxlen=self._maxlen))
        window.append(value)

    def z_score(self, key: WindowKey, value: float) -> float | None:
        """
        Compute the Z-score of `value` against the existing history.

        Note:
            This method assumes `value` has NOT yet been added to the window.
            Call `z_score()` before `push()` to avoid contaminating the
            statistical baseline with the sample being evaluated.
        """
        window = self._data.get(key)
        if not window or len(window) < self._min_samples:
            return None

        mean = statistics.fmean(window)
        stdev = statistics.pstdev(window)
        stdev = max(stdev, 1.0)  # floor: don't let a tight cluster inflate z-score artificially

        if stdev == 0:
            return 0.0

        return (value - mean) / stdev