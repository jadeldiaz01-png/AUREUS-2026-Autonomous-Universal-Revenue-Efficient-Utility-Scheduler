from aureus.runtime import RuntimeReadiness


def test_readiness_is_fail_closed() -> None:
    assert RuntimeReadiness(False, True, True, True, True, True).ready is False
    assert RuntimeReadiness(True, True, True, True, True, True).ready is True
