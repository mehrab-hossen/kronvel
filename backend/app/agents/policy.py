"""
Risk classification for proposed remediation actions.

Deliberately rule-based, NOT an LLM call — despite prompts/policy/ being
reserved in the original architecture sketch for an LLM-based classifier.
A policy gate is a security control; making it depend on LLM judgment would
introduce prompt-injection surface and non-determinism into the one
component specifically responsible for blocking unsafe actions. Deterministic
rules here are also trivially testable for both the allow AND block path,
which SECURITY.md and CONTRIBUTING.md both require for any change to this file.
"""
from enum import Enum


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    ALLOW_DRY_RUN_ONLY = "allow_dry_run_only"
    BLOCK = "block"


class ActionRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Actions this policy engine recognizes at all. Anything else is BLOCK by
# default — an unrecognized action is treated as maximally unsafe, never
# maximally permissive.
_KNOWN_ACTIONS = {"cordon", "uncordon"}

# Reversible, low-blast-radius actions cleared for live execution in the MVP
# once they also pass the dry_run gate at the remediation layer (Day 6).
_LIVE_ALLOWED_ACTIONS = {"cordon", "uncordon"}


class PolicyGate:
    def classify(self, action: str, node: str) -> tuple[PolicyDecision, ActionRiskLevel, str]:
        if action not in _KNOWN_ACTIONS:
            return (
                PolicyDecision.BLOCK,
                ActionRiskLevel.HIGH,
                f"Action '{action}' is not recognized by policy — blocked by default (see SECURITY.md).",
            )

        risk_level = ActionRiskLevel.LOW if action == "uncordon" else ActionRiskLevel.MEDIUM

        if action in _LIVE_ALLOWED_ACTIONS:
            return (
                PolicyDecision.ALLOW,
                risk_level,
                f"Action '{action}' on '{node}' is reversible and within the MVP's approved action set.",
            )

        return (
            PolicyDecision.ALLOW_DRY_RUN_ONLY,
            ActionRiskLevel.HIGH,
            f"Action '{action}' is recognized but not yet cleared for live execution.",
        )

