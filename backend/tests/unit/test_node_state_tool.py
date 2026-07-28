from datetime import datetime, timezone

import pytest

from app.agents.tools.node_state import NodeStateTool
from shared.schemas.node import NodeHealthStatus, NodeState


async def _fake_fetch_nodes() -> list[NodeState]:
    now = datetime.now(timezone.utc)
    return [
        NodeState(node="gpu-node-1", gpu_count=1, health_status=NodeHealthStatus.HEALTHY, gpus=[], updated_at=now),
        NodeState(node="gpu-node-6", gpu_count=1, health_status=NodeHealthStatus.CRITICAL, gpus=[], updated_at=now),
    ]


@pytest.mark.asyncio
async def test_node_state_tool_returns_all_nodes():
    tool = NodeStateTool(fetch_nodes=_fake_fetch_nodes)
    result = await tool.run()
    assert len(result) == 2


@pytest.mark.asyncio
async def test_node_state_tool_filters_by_node():
    tool = NodeStateTool(fetch_nodes=_fake_fetch_nodes)
    result = await tool.run(node="gpu-node-6")
    assert len(result) == 1
    assert result[0].health_status == NodeHealthStatus.CRITICAL

    