"""
ReAct-style tool-calling agent. Grounds answers in live tool results rather
than reasoning from parametric knowledge — the single most important
hallucination guard for an ops tool: never invent a node name or metric.

kubectl_action is forced into dry_run=True whenever it's called from this
loop, regardless of what the model requests or what the policy gate decides —
see the Day 5 guide's "One safety constraint" note. Live remediation is a
separate, explicit flow built Day 6, not a side effect of chat.
"""
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from app.agents.policy import PolicyGate
from app.agents.provider import LLMProvider
from app.agents.tools.kubectl import KubectlTool
from app.agents.tools.node_state import NodeStateTool
from app.agents.tools.prometheus import PrometheusTool
from app.prompts.registry import load_prompt

logger = logging.getLogger("kronvel.agents.copilot")

MAX_ITERATIONS = 6

_ALL_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "query_prometheus",
            "description": "Run a PromQL query against live cluster metrics and return current values.",
            "parameters": {
                "type": "object",
                "properties": {
                    "promql_query": {"type": "string", "description": "A valid PromQL query, e.g. DCGM_FI_DEV_GPU_TEMP"}
                },
                "required": ["promql_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_node_state",
            "description": "Return current health status and GPU telemetry for all cluster nodes, or a specific node.",
            "parameters": {
                "type": "object",
                "properties": {"node": {"type": "string", "description": "Optional node name to filter to a single node"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "kubectl_action",
            "description": (
                "Propose a scoped Kubernetes action (cordon/uncordon a node). Always executes as a "
                "policy-annotated dry run in this conversation — live execution requires the separate "
                "remediation confirmation flow."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["cordon", "uncordon"]},
                    "node": {"type": "string"},
                },
                "required": ["action", "node"],
            },
        },
    },
]


@dataclass
class AgentEvent:
    type: str  # "tool_call" | "tool_result" | "answer" | "error"
    payload: dict[str, Any] = field(default_factory=dict)


class CopilotAgent:
    def __init__(
        self,
        provider: LLMProvider,
        prometheus_tool: PrometheusTool,
        node_state_tool: NodeStateTool,
        kubectl_tool: KubectlTool | None,
        policy_gate: PolicyGate,
    ):
        self._provider = provider
        self._prometheus_tool = prometheus_tool
        self._node_state_tool = node_state_tool
        self._kubectl_tool = kubectl_tool
        self._policy_gate = policy_gate

        # kubectl_action is only offered to the model if a real tool instance exists —
        # never present a tool the agent can't actually use (e.g., no reachable cluster).
        if kubectl_tool is None:
            self._tool_schemas = [s for s in _ALL_TOOL_SCHEMAS if s["function"]["name"] != "kubectl_action"]
        else:
            self._tool_schemas = _ALL_TOOL_SCHEMAS

    async def run(self, user_message: str, history: list[dict[str, Any]] | None = None):
        """Async generator yielding AgentEvent objects as the ReAct loop progresses."""
        system_prompt = load_prompt("copilot/system_v1.jinja2")
        messages: list[dict[str, Any]] = list(history or [])
        messages.append({"role": "user", "content": user_message})

        for _ in range(MAX_ITERATIONS):
            try:
                response = await self._provider.create_message(
                    system=system_prompt, messages=messages, tools=self._tool_schemas
                )
            except Exception as exc:
                logger.exception("LLM call failed")
                yield AgentEvent(type="error", payload={"message": str(exc)})
                return

            message = response.choices[0].message
            tool_calls = message.tool_calls or []

            if not tool_calls:
                yield AgentEvent(type="answer", payload={"text": message.content or ""})
                return

            messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                        for tc in tool_calls
                    ],
                }
            )
            for tc in tool_calls:
                tool_input = json.loads(tc.function.arguments)
                yield AgentEvent(type="tool_call", payload={"tool": tc.function.name, "input": tool_input})
                result = await self._execute_tool(tc.function.name, tool_input)
                yield AgentEvent(type="tool_result", payload={"tool": tc.function.name, "result": result})
                messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result, default=str)}
                )

        yield AgentEvent(
            type="error",
            payload={"message": f"Reached the maximum of {MAX_ITERATIONS} reasoning steps without a final answer."},
        )

    async def _execute_tool(self, name: str, tool_input: dict[str, Any]) -> Any:
        if name == "query_prometheus":
            return await self._prometheus_tool.run(tool_input["promql_query"])

        if name == "get_node_state":
            nodes = await self._node_state_tool.run(node=tool_input.get("node"))
            return [n.model_dump(mode="json") for n in nodes]

        if name == "kubectl_action":
            if self._kubectl_tool is None:
                return {"error": "kubectl tool unavailable — no reachable cluster configured"}

            decision, risk, reason = self._policy_gate.classify(
                action=tool_input["action"], node=tool_input["node"]
            )
            # Forced dry_run=True regardless of policy decision — see module docstring.
            result = await self._kubectl_tool.run(action=tool_input["action"], node=tool_input["node"], dry_run=True)
            result["policy_decision"] = decision.value
            result["policy_risk_level"] = risk.value
            result["policy_reason"] = reason
            result["note"] = "Executed as dry-run only. Live execution requires the remediation confirmation flow."
            return result

        raise ValueError(f"Unknown tool: {name}")

