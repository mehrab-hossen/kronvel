from app.pipeline.processor import raw_to_gpu_metrics


def test_raw_to_gpu_metrics_assembles_complete_record():
    raw = {
        "DCGM_FI_DEV_GPU_TEMP": [{"metric": {"node": "gpu-node-1", "gpu": "0"}, "value": [0, "55.0"]}],
        "DCGM_FI_DEV_GPU_UTIL": [{"metric": {"node": "gpu-node-1", "gpu": "0"}, "value": [0, "40.0"]}],
        "DCGM_FI_DEV_FB_USED": [{"metric": {"node": "gpu-node-1", "gpu": "0"}, "value": [0, "4000.0"]}],
        "DCGM_FI_DEV_POWER_USAGE": [{"metric": {"node": "gpu-node-1", "gpu": "0"}, "value": [0, "120.0"]}],
        "DCGM_FI_DEV_XID_ERRORS": [{"metric": {"node": "gpu-node-1", "gpu": "0"}, "value": [0, "0"]}],
        "DCGM_FI_DEV_ECC_SBE_VOL_TOTAL": [{"metric": {"node": "gpu-node-1", "gpu": "0"}, "value": [0, "0"]}],
    }
    metrics = raw_to_gpu_metrics(raw)
    assert len(metrics) == 1
    assert metrics[0].node == "gpu-node-1"
    assert metrics[0].temperature_celsius == 55.0


def test_incomplete_series_is_skipped_not_crashed():
    raw = {
        "DCGM_FI_DEV_GPU_TEMP": [{"metric": {"node": "gpu-node-1", "gpu": "0"}, "value": [0, "55.0"]}],
        # All other metrics missing for this GPU — should be skipped, not raise.
    }
    metrics = raw_to_gpu_metrics(raw)
    assert metrics == []

    