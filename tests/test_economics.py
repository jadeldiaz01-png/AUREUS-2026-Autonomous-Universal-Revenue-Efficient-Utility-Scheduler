from decimal import Decimal

from aureus.domain import CostBreakdown, Opportunity
from aureus.economics import assess


def test_expected_net_profit_uses_utilization_and_payment_probability() -> None:
    opportunity = Opportunity(
        provider="test",
        resource_id="gpu-1",
        gross_revenue_usd=Decimal("10"),
        expected_utilization=Decimal("0.8"),
        payment_probability=Decimal("0.9"),
        costs=CostBreakdown(energy=Decimal("1.2"), depreciation=Decimal("0.8")),
    )
    result = assess(opportunity)
    assert result.expected_gross_usd == Decimal("7.20")
    assert result.expected_net_usd == Decimal("5.20")
    assert result.profitable is True
