from decimal import Decimal

from aureus.providers import RunPodObserver, VastObserver
from aureus.readiness import ProductionEvidence, ReadinessDecision, SettlementWindow, evaluate


def base_evidence(*windows: SettlementWindow) -> ProductionEvidence:
    return ProductionEvidence(
        engineering_green=True,
        database_ready=True,
        pitr_restore_verified=True,
        workload_identity_verified=True,
        otlp_healthy=True,
        provider_observer_certified=True,
        runtime_ready=True,
        positive_windows=tuple(windows),
    )


def good_window(value: str = "1.00") -> SettlementWindow:
    return SettlementWindow(
        net_cash_usd=Decimal(value),
        telemetry_coverage=Decimal("0.99"),
        unresolved_cost_items=0,
        externally_verified=True,
    )


def test_internal_or_unverified_earnings_cannot_grant_production_go():
    fake = SettlementWindow(Decimal("1000"), Decimal("1"), 0, externally_verified=False)
    assert evaluate(base_evidence(fake, fake, fake, fake)) is ReadinessDecision.CONDITIONAL_GO


def test_unresolved_costs_cannot_grant_production_go():
    bad = SettlementWindow(Decimal("10"), Decimal("1"), 1, externally_verified=True)
    assert evaluate(base_evidence(bad, bad, bad)) is ReadinessDecision.CONDITIONAL_GO


def test_low_telemetry_coverage_cannot_grant_production_go():
    bad = SettlementWindow(Decimal("10"), Decimal("0.94"), 0, externally_verified=True)
    assert evaluate(base_evidence(bad, bad, bad)) is ReadinessDecision.CONDITIONAL_GO


def test_three_independent_qualified_windows_are_required():
    assert evaluate(base_evidence(good_window(), good_window())) is ReadinessDecision.CONDITIONAL_GO
    assert evaluate(base_evidence(good_window(), good_window(), good_window())) is ReadinessDecision.GO


def test_observer_interfaces_do_not_expose_provider_write_methods():
    forbidden = {"create", "delete", "rent", "terminate", "withdraw", "payout", "transfer", "start", "stop"}
    vast_methods = {name.lower() for name in dir(VastObserver)}
    runpod_methods = {name.lower() for name in dir(RunPodObserver)}
    assert not (forbidden & vast_methods)
    assert not (forbidden & runpod_methods)
    assert VastObserver.capabilities.machine_write is False
    assert VastObserver.capabilities.billing_write is False
