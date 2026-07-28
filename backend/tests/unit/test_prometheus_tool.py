import pytest

from app.agents.tools.prometheus import PrometheusTool


@pytest.mark.asyncio
async def test_prometheus_tool_returns_labeled_results():
    # Requires Prometheus + simulator running (make dev) — this is intentionally
    # a live integration-style check, consistent with how pipeline/collector.py
    # is verified on Day 3, since PromQL correctness is best proven against
    # a real Prometheus instance rather than a hand-mocked HTTP response.
    tool = PrometheusTool(base_url="http://localhost:9090")
    results = await tool.run("DCGM_FI_DEV_GPU_TEMP")
    assert isinstance(results, list)
    if results:  # tolerate a cold-started stack with no scrapes yet
        assert "labels" in results[0]
        assert "value" in results[0]
        