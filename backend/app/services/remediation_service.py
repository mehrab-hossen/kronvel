"""
Orchestrates policy -> dry_run -> kubectl -> audit. Every call through this
service writes an action_audit record regardless of outcome — approved,
blocked, or failed during execution are all first-class outcomes here, not
just successful executions. This is the platform's central safety mechanism;
see the Day 6 guide's "Common Mistakes to Avoid" before modifying dry_run
resolution logic specifically.
"""

import logging
import uuid

from app.agents.policy import PolicyDecision, PolicyGate
from app.agents.tools.kubectl import KubectlTool
from app.core.config import get_settings
from app.core.exceptions import ActionBlockedError, RepositoryError
from app.models.action_audit import ActionAudit
from app.repositories.postgres_repository import (
    PostgresActionAuditRepository,
    PostgresNodeRepository,
)

logger = logging.getLogger("kronvel.services.remediation")


class RemediationService:
    def __init__(
        self,
        policy_gate: PolicyGate,
        kubectl_tool: KubectlTool | None,
        audit_repo: PostgresActionAuditRepository,
        node_repo: PostgresNodeRepository,
        repeat_guard,

    ):
        self._policy_gate = policy_gate
        self._kubectl_tool = kubectl_tool
        self._audit_repo = audit_repo
        self._node_repo = node_repo
        self._repeat_guard = repeat_guard
        self._settings = get_settings()


    async def execute(
        self,
        action: str,
        node: str,
        dry_run: bool | None = None,
        requested_by: str = "operator",
    ) -> ActionAudit:
        audit_id = str(uuid.uuid4())
        decision, risk, reason = self._policy_gate.classify(
            action=action,
            node=node,
        )

        # dry_run resolution: the caller's explicit choice is honored ONLY when
        # policy fully allows live execution. Policy can force a STRICTER value
        # (True), never a looser one.
        effective_dry_run = (
            dry_run
            if dry_run is not None
            else self._settings.dry_run_default
        )

        if decision != PolicyDecision.ALLOW:
            effective_dry_run = True

        audit = ActionAudit(
            id=audit_id,
            action=action,
            node=node,
            requested_by=requested_by,
            dry_run=effective_dry_run,
            policy_decision=decision.value,
            policy_risk_level=risk.value,
            policy_reason=reason,
            executed=False,
        )

        if decision == PolicyDecision.BLOCK:
            await self._safe_save(audit_id, audit)
            raise ActionBlockedError(reason)

        if action == "cordon":

            guard = self._repeat_guard.check(
                node=node,
                action=action,
            )

            if not guard["allowed"]:
                audit.error = (
                    "Repeat guard blocked remediation. "
                    f"Attempts={guard['attempts']}/"
                    f"{guard['limit']}. "
                    "Human review required."
                )

                audit.result = {
                    "status": "blocked",
                    "reason": "repeat_guard_triggered",
                    "attempts": guard["attempts"],
                    "limit": guard["limit"],
                    "requires_human_review": True,
                }

                await self._safe_save(
                    audit_id,
                    audit,
                )

                return audit

        if self._kubectl_tool is None:
            audit.error = (
                "kubectl tool unavailable — no reachable cluster configured"
            )
            await self._safe_save(audit_id, audit)
            return audit

        try:
            result = await self._kubectl_tool.run(
                action=action,
                node=node,
                dry_run=effective_dry_run,
            )
            audit.executed = result.get("executed", False)
            audit.result = result

            if audit.executed and not effective_dry_run:
                if action == "cordon":
                    await self._node_repo.set_cordoned(
                        node=node,
                        cordoned=True,
                    )

                elif action == "uncordon":
                    await self._node_repo.set_cordoned(
                        node=node,
                        cordoned=False,
                    )

        except Exception as exc:
            logger.exception(
                "Remediation execution failed for action=%s node=%s",
                action,
                node,
            )
            audit.error = str(exc)

        await self._safe_save(audit_id, audit)
        return audit

    async def get_history(
        self,
        node: str | None = None,
    ) -> list[ActionAudit]:
        filters = {"node": node} if node else {}
        return await self._audit_repo.list(**filters)

    async def _safe_save(
        self,
        audit_id: str,
        audit: ActionAudit,
    ) -> None:
        try:
            await self._audit_repo.save(audit_id, audit)
        except RepositoryError:
            logger.exception(
                "CRITICAL: failed to persist action_audit %s for action=%s "
                "node=%s executed=%s — audit trail is incomplete for this action",
                audit_id,
                audit.action,
                audit.node,
                audit.executed,
            )
            raise

        