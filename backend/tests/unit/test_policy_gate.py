from app.agents.policy import ActionRiskLevel, PolicyDecision, PolicyGate


def test_policy_allows_cordon():
    gate = PolicyGate()
    decision, risk, reason = gate.classify(action="cordon", node="gpu-node-6")
    assert decision == PolicyDecision.ALLOW
    assert risk == ActionRiskLevel.MEDIUM
    assert "gpu-node-6" in reason


def test_policy_allows_uncordon_as_low_risk():
    gate = PolicyGate()
    decision, risk, _ = gate.classify(action="uncordon", node="gpu-node-6")
    assert decision == PolicyDecision.ALLOW
    assert risk == ActionRiskLevel.LOW


def test_policy_blocks_unknown_action_by_default():
    gate = PolicyGate()
    decision, risk, reason = gate.classify(action="delete", node="gpu-node-6")
    assert decision == PolicyDecision.BLOCK
    assert risk == ActionRiskLevel.HIGH
    assert "not recognized" in reason
    