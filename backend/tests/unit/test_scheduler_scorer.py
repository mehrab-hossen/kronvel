from datetime import datetime, timezone

from app.ml.scheduler.scorer import HeuristicScheduler
from shared.schemas.node import GPUMetric, NodeHealthStatus, NodeState


def _node(temp=50.0, util=30.0, health=NodeHealthStatus.HEALTHY, name="gpu-node-1") -> NodeState:
    gpu = GPUMetric(
        node=name, gpu_index="0", temperature_celsius=temp, utilization_percent=util,
        memory_used_mib=4000, power_watts=120, xid_error_code=0, ecc_sbe_total=0,
        observed_at=datetime.now(timezone.utc),
    )
    return NodeState(node=name, gpu_count=1, health_status=health, gpus=[gpu], updated_at=datetime.now(timezone.utc))


def test_healthy_low_utilization_node_scores_highest():
    scheduler = HeuristicScheduler()
    nodes = [
        _node(temp=50, util=20, health=NodeHealthStatus.HEALTHY, name="cool-idle"),
        _node(temp=70, util=90, health=NodeHealthStatus.HEALTHY, name="hot-busy"),
    ]
    scores = scheduler.score(nodes)
    assert scores[0].node == "cool-idle"
    assert scores[0].score > scores[1].score


def test_critical_node_scores_zero():
    scheduler = HeuristicScheduler()
    nodes = [_node(temp=95, util=80, health=NodeHealthStatus.CRITICAL, name="dying-node")]
    scores = scheduler.score(nodes)
    assert scores[0].score == 0.0


def test_degraded_node_penalized_relative_to_healthy():
    scheduler = HeuristicScheduler()
    nodes = [
        _node(temp=50, util=30, health=NodeHealthStatus.HEALTHY, name="healthy-node"),
        _node(temp=50, util=30, health=NodeHealthStatus.DEGRADED, name="degraded-node"),
    ]
    scores = scheduler.score(nodes)
    healthy_score = next(s.score for s in scores if s.node == "healthy-node")
    degraded_score = next(s.score for s in scores if s.node == "degraded-node")
    assert healthy_score > degraded_score
    