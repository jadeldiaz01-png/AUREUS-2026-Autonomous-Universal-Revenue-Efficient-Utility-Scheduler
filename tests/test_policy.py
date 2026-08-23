from decimal import Decimal

from aureus.domain import CostBreakdown, Decision, Opportunity
from aureus.policy import PolicyContext, decide


def opportunity(**overrides: object) -> Opportunity:
    values: dict[str, object] = {
        "provider": "vast",
        "resource_id": "gpu-1",
        "gross_revenue_usd": Decimal("10"),
        "expected_utilization": Decimal("1"),
        "payment_probability": Decimal("1"),
        "costs": CostBreakdown(energy=Decimal("1")),
        "authorized_resource": True,
        "tos_allowed": True,
        "geo_allowed": True,
        "risk_allowed": True,
    }
    values.update(overrides)
    return Opportunity(**values)  # type: ignore[arg-type]


def test_kill_switch_precedes_profit() -> None:
    assert decide(opportunity(), PolicyContext(kill_switch=True)) == Decision.REJECT


def test_unauthorized_compute_is_rejected() -> None:
    assert decide(opportunity(authorized_resource=False), PolicyContext()) == Decision.REJECT


def test_positive_candidate_remains_simulation_until_certified_and_enabled() -> None:
    assert decide(opportunity(), PolicyContext(provider_certified=False, external_execution_enabled=False)) == Decision.SIMULATE


def test_even_certified_external_candidate_requires_human_boundary() -> None:
    context = PolicyContext(provider_certified=True, external_execution_enabled=True)
    assert decide(opportunity(), context) == Decision.HUMAN_REQUIRED
