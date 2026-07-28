from app.services.repeat_guard_service import RepeatGuard


def test_repeat_guard_blocks_repeated_actions():

    guard = RepeatGuard(max_attempts=3)

    assert guard.check(
        "gpu-node-6",
        "cordon",
    )["allowed"]

    assert guard.check(
        "gpu-node-6",
        "cordon",
    )["allowed"]

    assert guard.check(
        "gpu-node-6",
        "cordon",
    )["allowed"]

    result = guard.check(
        "gpu-node-6",
        "cordon",
    )

    assert result["allowed"] is False
    