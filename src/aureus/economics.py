from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .domain import Opportunity


@dataclass(frozen=True)
class EconomicAssessment:
    expected_gross_usd: Decimal
    expected_net_usd: Decimal
    profitable: bool


def assess(opportunity: Opportunity) -> EconomicAssessment:
    if not Decimal("0") <= opportunity.expected_utilization <= Decimal("1"):
        raise ValueError("expected_utilization must be in [0,1]")
    if not Decimal("0") <= opportunity.payment_probability <= Decimal("1"):
        raise ValueError("payment_probability must be in [0,1]")
    expected_gross = opportunity.gross_revenue_usd * opportunity.expected_utilization * opportunity.payment_probability
    expected_net = expected_gross - opportunity.costs.total
    return EconomicAssessment(expected_gross, expected_net, expected_net > 0)
