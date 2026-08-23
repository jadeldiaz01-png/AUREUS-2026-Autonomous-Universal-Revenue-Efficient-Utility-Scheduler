from aureus.providers import VastObserver


def test_vast_observer_has_no_write_authority() -> None:
    assert VastObserver.capabilities.machine_read is True
    assert VastObserver.capabilities.billing_read is True
    assert VastObserver.capabilities.machine_write is False
    assert VastObserver.capabilities.billing_write is False
    assert not hasattr(VastObserver, "create_machine")
    assert not hasattr(VastObserver, "request_payout")
