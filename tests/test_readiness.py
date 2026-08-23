from decimal import Decimal

from aureus.readiness import ProductionEvidence, ReadinessDecision, SettlementWindow, evaluate


def evidence(windows: tuple[SettlementWindow, ...]) -> ProductionEvidence:
    return ProductionEvidence(True, True, True, True, True, True, True, windows)


def test_three_independent_positive_windows_are_required_for_go() -> None:
    good = SettlementWindow(Decimal("5"), Decimal("0.99"), 0, True)
    assert evaluate(evidence((good, good))) is ReadinessDecision.CONDITIONAL_GO
    assert evaluate(evidence((good, good, good))) is ReadinessDecision.GO


def test_unresolved_costs_block_window() -> None:
    bad = SettlementWindow(Decimal("5"), Decimal("0.99"), 1, True)
    assert evaluate(evidence((bad, bad, bad))) is ReadinessDecision.CONDITIONAL_GO
