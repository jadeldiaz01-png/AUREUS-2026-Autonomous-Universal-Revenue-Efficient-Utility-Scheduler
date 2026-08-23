from __future__ import annotations

from dataclasses import dataclass

from .domain import Decision, Opportunity
from .economics import EconomicAssessment, assess
from .policy import PolicyContext, decide


@dataclass(frozen=True)
class RankedOpportunity:
    opportunity: Opportunity
    economics: EconomicAssessment
    decision: Decision


class RevenueSupervisor:
    def rank(self, opportunities: list[Opportunity], context: PolicyContext) -> list[RankedOpportunity]:
        ranked = [RankedOpportunity(o, assess(o), decide(o, context)) for o in opportunities]
        return sorted(ranked, key=lambda item: item.economics.expected_net_usd, reverse=True)
