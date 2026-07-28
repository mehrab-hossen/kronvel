"""
Baseline anomaly detector: rule-based checks for hard-fault signals (XID, ECC)
combined with a statistical rolling-window check for thermal drift.

This is a deliberate MVP scope decision: a trained ML model is NOT required to
prove the product thesis and would cost a full day better spent on the
remediation + audit trail loop (see docs/ROADMAP.md MVP scope). This detector
is the thing a trained model would eventually replace — same interface,
swappable implementation.
"""
from shared.schemas.anomaly import Anomaly, AnomalySeverity, AnomalyType
from shared.schemas.node import GPUMetric

from app.ml.anomaly.features import RollingWindow, WindowKey


class AnomalyDetector:
    def __init__(
        self,
        temp_z_threshold: float = 3.0,
        temp_absolute_threshold_c: float = 85.0,
        temp_critical_threshold_c: float = 95.0,
        window_size: int = 15,
    ):
        self._temp_window = RollingWindow(maxlen=window_size)
        self._last_ecc: dict[WindowKey, int] = {}
        self._temp_z_threshold = temp_z_threshold
        self._temp_absolute_threshold_c = temp_absolute_threshold_c
        self._temp_critical_threshold_c = temp_critical_threshold_c

    def evaluate(self, metric: GPUMetric) -> Anomaly | None:
        key: WindowKey = (metric.node, metric.gpu_index)

        xid_anomaly = self._check_xid(metric)
        if xid_anomaly:
            return xid_anomaly

        ecc_anomaly = self._check_ecc(metric, key)
        if ecc_anomaly:
            return ecc_anomaly

        return self._check_thermal(metric, key)

    def _check_xid(self, metric: GPUMetric) -> Anomaly | None:
        if metric.xid_error_code == 0:
            return None
        return Anomaly(
            node=metric.node,
            gpu_index=metric.gpu_index,
            anomaly_type=AnomalyType.XID_ERROR,
            severity=AnomalySeverity.CRITICAL,
            metric_value=float(metric.xid_error_code),
            threshold=0.0,
            description=f"XID error code {metric.xid_error_code} reported on {metric.node} (gpu {metric.gpu_index})",
            detected_at=metric.observed_at,
        )

    def _check_ecc(self, metric: GPUMetric, key: WindowKey) -> Anomaly | None:
        previous = self._last_ecc.get(key, metric.ecc_sbe_total)
        self._last_ecc[key] = metric.ecc_sbe_total
        if metric.ecc_sbe_total <= previous:
            return None
        delta = metric.ecc_sbe_total - previous
        severity = AnomalySeverity.HIGH if delta >= 3 else AnomalySeverity.MEDIUM
        return Anomaly(
            node=metric.node,
            gpu_index=metric.gpu_index,
            anomaly_type=AnomalyType.ECC_ERROR,
            severity=severity,
            metric_value=float(metric.ecc_sbe_total),
            threshold=float(previous),
            description=f"{delta} new ECC single-bit error(s) on {metric.node} (gpu {metric.gpu_index})",
            detected_at=metric.observed_at,
        )

    def _check_thermal(self, metric: GPUMetric, key: WindowKey) -> Anomaly | None:
        z = self._temp_window.z_score(key, metric.temperature_celsius)
        self._temp_window.push(key, metric.temperature_celsius)  # push AFTER computing z

        breached_absolute = metric.temperature_celsius >= self._temp_absolute_threshold_c
        breached_z = z is not None and z >= self._temp_z_threshold

        if not (breached_absolute or breached_z):
            return None

        severity = (
            AnomalySeverity.CRITICAL
            if metric.temperature_celsius >= self._temp_critical_threshold_c
            else AnomalySeverity.HIGH
        )
        z_display = f"{z:.2f}" if z is not None else "n/a"
        return Anomaly(
            node=metric.node,
            gpu_index=metric.gpu_index,
            anomaly_type=AnomalyType.THERMAL,
            severity=severity,
            metric_value=metric.temperature_celsius,
            threshold=self._temp_absolute_threshold_c,
            description=(
                f"Thermal anomaly on {metric.node} (gpu {metric.gpu_index}): "
                f"{metric.temperature_celsius:.1f}\u00b0C (z-score={z_display})"
            ),
            detected_at=metric.observed_at,
        )