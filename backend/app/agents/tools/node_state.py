"""
Agent tool: current cluster node/GPU state, for Copilot investigation.

Depends on an injected fetch callable (typically AnomalyService.list_nodes)
rather than importing AnomalyService directly, so this tool is trivially
unit-testable with a fake in tests/unit — see test_node_state_tool.py.
"""
from typing import Awaitable, Callable

from shared.schemas.node import NodeState

NodeStateFetcher = Callable[[], Awaitable[list[NodeState]]]


class NodeStateTool:
    name = "get_node_state"
    description = "Return current health status and GPU telemetry for all cluster nodes, or a specific node."

    def __init__(self, fetch_nodes: NodeStateFetcher):
        self._fetch_nodes = fetch_nodes

    async def run(self, node: str | None = None) -> list[NodeState]:
        nodes = await self._fetch_nodes()
        if node:
            return [n for n in nodes if n.node == node]
        return nodes
    