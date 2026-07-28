from datetime import datetime, timezone

from app.ml.anomaly.detector import AnomalyDetector
from shared.schemas.node import GPUMetric


def _metric(temp=50.0, xid=0, ecc=0, node="gpu-node-1", gpu="0") -> GPUMetric:
    return GPUMetric(
        node=node, gpu_index=gpu, temperature_celsius=temp, utilization_percent=30.0,
        memory_used_mib=4000.0, power_watts=120.0, xid_error_code=xid, ecc_sbe_total=ecc,
        observed_at=datetime.now(timezone.utc),
    )


def test_xid_error_always_flagged():
    detector = AnomalyDetector()
    result = detector.evaluate(_metric(xid=79))
    assert result is not None
    assert result.anomaly_type.value == "xid_error"
    assert result.severity.value == "critical"


def test_ecc_increase_flagged_but_first_observation_is_not():
    detector = AnomalyDetector()
    first = detector.evaluate(_metric(ecc=0))
    assert first is None  # baseline observation, no prior value to compare against

    second = detector.evaluate(_metric(ecc=2))
    assert second is not None
    assert second.anomaly_type.value == "ecc_error"


def test_stable_normal_temperature_never_flagged():
    detector = AnomalyDetector()
    result = None
    for _ in range(20):
        result = detector.evaluate(_metric(temp=50.0))
    assert result is None


def test_thermal_spike_flagged_via_absolute_threshold():
    detector = AnomalyDetector(temp_absolute_threshold_c=85.0)
    for _ in range(6):
        detector.evaluate(_metric(temp=50.0))
    result = detector.evaluate(_metric(temp=95.0))
    assert result is not None
    assert result.anomaly_type.value == "thermal"
    assert result.severity.value == "critical"


def test_thermal_flagged_via_z_score_before_absolute_threshold():
    detector = AnomalyDetector(
        temp_absolute_threshold_c=85.0,
        temp_z_threshold=2.0,
    )

    baseline = [
        49.8,
        50.2,
        49.9,
        50.1,
        50.0,
        49.7,
        50.3,
        49.9,
    ]

    for temp in baseline:
        detector.evaluate(_metric(temp=temp))

    result = detector.evaluate(_metric(temp=65.0))

    assert result is not None
    assert result.anomaly_type.value == "thermal"


def test_different_gpus_tracked_independently():
    detector = AnomalyDetector()
    detector.evaluate(_metric(ecc=0, gpu="0"))
    result_gpu1 = detector.evaluate(_metric(ecc=0, gpu="1"))
    assert result_gpu1 is None  # gpu "1" has its own independent baseline