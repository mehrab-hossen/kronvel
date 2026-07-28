import pytest

from app.agents.policy import PolicyGate
from app.core.exceptions import ActionBlockedError
from app.models.action_audit import ActionAudit
from app.services.remediation_service import RemediationService


class InMemoryAuditRepo:
    def __init__(self):
        self.store: dict[str, ActionAudit] = {}

    async def get(self, key: str) -> ActionAudit | None:
        return self.store.get(key)

    async def save(self, key: str, item: ActionAudit) -> None:
        self.store[key] = item

    async def list(self, **filters) -> list[ActionAudit]:
        return list(self.store.values())

    async def delete(self, key: str) -> None:
        self.store.pop(key, None)


class FakeKubectlTool:
    def __init__(self, raise_on_run: bool = False):
        self.calls: list[tuple[str, str, bool]] = []
        self._raise_on_run = raise_on_run

    async def run(self, action: str, node: str, dry_run: bool = True) -> dict:
        self.calls.append((action, node, dry_run))
        if self._raise_on_run:
            raise RuntimeError("simulated cluster API failure")
        return {"node": node, "action": action, "dry_run": dry_run, "executed": not dry_run}


@pytest.mark.asyncio
async def test_blocked_action_raises_and_still_writes_audit():
    audit_repo = InMemoryAuditRepo()
    service = RemediationService(policy_gate=PolicyGate(), kubectl_tool=FakeKubectlTool(), audit_repo=audit_repo)

    with pytest.raises(ActionBlockedError):
        await service.execute(action="delete", node="gpu-node-1")

    assert len(audit_repo.store) == 1
    saved = list(audit_repo.store.values())[0]
    assert saved.policy_decision == "block"
    assert saved.executed is False


@pytest.mark.asyncio
async def test_allowed_action_defaults_to_dry_run():
    audit_repo = InMemoryAuditRepo()
    kubectl = FakeKubectlTool()
    service = RemediationService(policy_gate=PolicyGate(), kubectl_tool=kubectl, audit_repo=audit_repo)

    result = await service.execute(action="cordon", node="gpu-node-1")

    assert result.dry_run is True
    assert result.executed is False
    assert kubectl.calls[0] == ("cordon", "gpu-node-1", True)


@pytest.mark.asyncio
async def test_allowed_action_executes_live_when_explicitly_requested():
    audit_repo = InMemoryAuditRepo()
    kubectl = FakeKubectlTool()
    service = RemediationService(policy_gate=PolicyGate(), kubectl_tool=kubectl, audit_repo=audit_repo)

    result = await service.execute(action="cordon", node="gpu-node-1", dry_run=False)

    assert result.dry_run is False
    assert result.executed is True


@pytest.mark.asyncio
async def test_blocked_action_cannot_be_forced_live():
    # Even if a caller explicitly requests dry_run=False, a BLOCKed action must never reach kubectl.
    audit_repo = InMemoryAuditRepo()
    kubectl = FakeKubectlTool()
    service = RemediationService(policy_gate=PolicyGate(), kubectl_tool=kubectl, audit_repo=audit_repo)

    with pytest.raises(ActionBlockedError):
        await service.execute(action="delete", node="gpu-node-1", dry_run=False)

    assert len(kubectl.calls) == 0  # kubectl was never called at all


@pytest.mark.asyncio
async def test_execution_failure_is_captured_in_audit_not_raised():
    audit_repo = InMemoryAuditRepo()
    kubectl = FakeKubectlTool(raise_on_run=True)
    service = RemediationService(policy_gate=PolicyGate(), kubectl_tool=kubectl, audit_repo=audit_repo)

    result = await service.execute(action="cordon", node="gpu-node-1", dry_run=False)

    assert result.error is not None
    assert "simulated cluster API failure" in result.error


@pytest.mark.asyncio
async def test_unavailable_kubectl_tool_is_recorded_not_crashed():
    audit_repo = InMemoryAuditRepo()
    service = RemediationService(policy_gate=PolicyGate(), kubectl_tool=None, audit_repo=audit_repo)

    result = await service.execute(action="cordon", node="gpu-node-1")

    assert result.error is not None
    assert "unavailable" in result.error
    