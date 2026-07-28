"""
Heuristic node placement scorer. Deliberately not a trained model — same MVP
scope decision as ml/anomaly/detector.py (see docs/ROADMAP.md). Higher score
means a better placement candidate. This is the thing a trained model would
eventually replace; the interface (score(nodes) -> list[NodeScore]) is
designed to make that swap a non-event later.
"""
from shared.schemas.node import NodeHealthStatus, NodeState
from shared.schemas.scheduler import NodeScore


class HeuristicScheduler:
    def score(self, nodes: list[NodeState]) -> list[NodeScore]:
        scores = [self._score_node(n) for n in nodes]
        return sorted(scores, key=lambda s: s.score, reverse=True)

    def _score_node(self, node: NodeState) -> NodeScore:
        if not node.gpus:
            return NodeScore(node=node.node, score=0.0, reasons=["no GPU telemetry available"])

        gpu = node.gpus[0]
        reasons: list[str] = []
        base = 100.0

        util_penalty = gpu.utilization_percent * 0.5
        base -= util_penalty
        reasons.append(f"utilization {gpu.utilization_percent:.0f}% (-{util_penalty:.1f})")

        if gpu.temperature_celsius > 60:
            temp_penalty = (gpu.temperature_celsius - 60) * 1.5
            base -= temp_penalty
            reasons.append(f"temperature {gpu.temperature_celsius:.0f}\u00b0C (-{temp_penalty:.1f})")

        if node.health_status == NodeHealthStatus.CRITICAL:
            base = 0.0
            reasons.append("health critical — excluded from placement")
        elif node.health_status == NodeHealthStatus.DEGRADED:
            base *= 0.3
            reasons.append("health degraded — heavily penalized")

        score = max(0.0, min(100.0, base))
        return NodeScore(node=node.node, score=round(score, 1), reasons=reasons)
    