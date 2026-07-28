from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pytest

from app.agents.copilot import CopilotAgent
from app.agents.policy import PolicyGate
from shared.schemas.node import NodeHealthStatus, NodeState


@dataclass
class FakeFunctionCall:
    name: str
    arguments: str = "{}"  # JSON-encoded string, mirrors OpenAI's function.arguments


@dataclass
class FakeToolCall:
    id: str
    function: FakeFunctionCall
    type: str = "function"


@dataclass
class FakeMessage:
    content: str | None = None
    tool_calls: list[FakeToolCall] = field(default_factory=list)


@dataclass
class FakeChoice:
    message: FakeMessage


@dataclass
class FakeResponse:
    choices: list[FakeChoice]


def _tool_call_response(name: str, tool_call_id: str = "t1", arguments: str = "{}") -> FakeResponse:
    return FakeResponse(
        choices=[
            FakeChoice(
                message=FakeMessage(
                    content=None,
                    tool_calls=[FakeToolCall(id=tool_call_id, function=FakeFunctionCall(name=name, arguments=arguments))],
                )
            )
        ]
    )


def _text_response(text: str) -> FakeResponse:
    return FakeResponse(choices=[FakeChoice(message=FakeMessage(content=text, tool_calls=[]))])


class FakeProvider:
    """Returns pre-scripted responses in order — no real API call."""

    def __init__(self, responses: list[FakeResponse]):
        self._responses = responses
        self.call_count = 0

    async def create_message(self, system: str, messages: list[dict[str, Any]], tools=None, max_tokens=1024):
        response = self._responses[self.call_count]
        self.call_count += 1
        return response


class FakeNodeStateTool:
    async def run(self, node: str | None = None) -> list[NodeState]:
        return [
            NodeState(
                node="gpu-node-6", gpu_count=1, health_status=NodeHealthStatus.CRITICAL,
                gpus=[], updated_at=datetime.now(timezone.utc),
            )
        ]


class FakePrometheusTool:
    async def run(self, promql_query: str) -> list[dict]:
        return [{"labels": {"node": "gpu-node-6"}, "value": "95.0"}]


@pytest.mark.asyncio
async def test_copilot_agent_grounds_answer_in_tool_result():
    tool_call_response = _tool_call_response("get_node_state", tool_call_id="t1")
    final_response = _text_response("gpu-node-6 is critical due to a thermal anomaly.")
    provider = FakeProvider([tool_call_response, final_response])

    agent = CopilotAgent(
        provider=provider,
        prometheus_tool=FakePrometheusTool(),
        node_state_tool=FakeNodeStateTool(),
        kubectl_tool=None,
        policy_gate=PolicyGate(),
    )

    events = [event async for event in agent.run("why is node-6 unhealthy?")]
    types = [e.type for e in events]

    assert "tool_call" in types
    assert "tool_result" in types
    assert types[-1] == "answer"
    assert "gpu-node-6" in events[-1].payload["text"]


@pytest.mark.asyncio
async def test_copilot_agent_hits_iteration_cap_gracefully():
    # Provider always returns a tool call, never a final answer — the loop must terminate anyway.
    infinite_tool_call = _tool_call_response("get_node_state", tool_call_id="t1")
    provider = FakeProvider([infinite_tool_call] * 10)

    agent = CopilotAgent(
        provider=provider,
        prometheus_tool=FakePrometheusTool(),
        node_state_tool=FakeNodeStateTool(),
        kubectl_tool=None,
        policy_gate=PolicyGate(),
    )

    events = [event async for event in agent.run("loop forever")]
    assert events[-1].type == "error"


@pytest.mark.asyncio
async def test_copilot_agent_excludes_kubectl_tool_when_unavailable():
    agent = CopilotAgent(
        provider=FakeProvider([]),
        prometheus_tool=FakePrometheusTool(),
        node_state_tool=FakeNodeStateTool(),
        kubectl_tool=None,
        policy_gate=PolicyGate(),
    )
    tool_names = [t["function"]["name"] for t in agent._tool_schemas]
    assert "kubectl_action" not in tool_names

