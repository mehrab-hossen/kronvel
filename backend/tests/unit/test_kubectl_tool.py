import os

import pytest

from app.agents.tools.kubectl import KubectlTool


@pytest.mark.asyncio
async def test_kubectl_tool_rejects_non_allowlisted_action():
    tool = KubectlTool.__new__(KubectlTool)  # allowlist check happens before any cluster call
    with pytest.raises(ValueError):
        await tool.run(action="delete", node="gpu-node-1")


@pytest.mark.asyncio
async def test_kubectl_tool_dry_run_never_touches_cluster():
    tool = KubectlTool.__new__(KubectlTool)
    result = await tool.run(action="cordon", node="gpu-node-1", dry_run=True)
    assert result["dry_run"] is True
    assert result["executed"] is False


@pytest.mark.skipif(
    not os.getenv("KRONVEL_TEST_KUBECONFIG"),
    reason="Requires a live kind cluster — set KRONVEL_TEST_KUBECONFIG to run this test",
)
@pytest.mark.asyncio
async def test_kubectl_tool_live_cordon_and_uncordon():
    tool = KubectlTool(kubeconfig_path=os.environ["KRONVEL_TEST_KUBECONFIG"])
    node_name = os.getenv("KRONVEL_TEST_NODE", "kronvel-dev-control-plane")
    result = await tool.run(action="cordon", node=node_name, dry_run=False)
    assert result["executed"] is True
    await tool.run(action="uncordon", node=node_name, dry_run=False)  # reset state
    