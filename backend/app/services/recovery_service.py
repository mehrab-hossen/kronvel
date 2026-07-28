from collections import defaultdict


class RecoveryScoreService:
    """
    Tracks gradual node recovery confidence.

    Score behavior:
    - Healthy node: +10
    - Unhealthy node: -20

    Range:
    0 - 100
    """

    def __init__(
        self,
        recovery_increment: int = 10,
        failure_decrement: int = 20,
    ):
        self.recovery_increment = recovery_increment
        self.failure_decrement = failure_decrement

        self._scores = defaultdict(lambda: 100)


    def update(
        self,
        node: str,
        healthy: bool,
    ) -> int:

        current = self._scores[node]

        if healthy:
            current += self.recovery_increment

        else:
            current -= self.failure_decrement

            # Keep demo failures meaningful without destroying recovery visualization
            current = max(
                40,
                current,
            )

        current = max(
            0,
            min(
                100,
                current,
            ),
        )

        self._scores[node] = current

        return current


    def get_score(
        self,
        node: str,
    ) -> int:

        return self._scores[node]


    def get_all(self) -> dict[str, int]:

        return dict(self._scores)

    