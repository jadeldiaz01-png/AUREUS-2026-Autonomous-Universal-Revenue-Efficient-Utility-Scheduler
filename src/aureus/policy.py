from __future__ import annotations

from dataclasses import dataclass

from .domain import Decision, Opportunity
from .economics import assess


@dataclass(frozen=True)
class PolicyContext:
    provider_certified: bool = False
    external_execution_enabled: bool = False
    kill_switch: bool = False


def decide(opportunity: Opportunity, context: PolicyContext) -> Decision:
    if context.kill_switch:
        return Decision.REJECT
    if not opportunity.authorized_resource:
        return Decision.REJECT
    if not (opportunity.tos_allowed and opportunity.geo_allowed and opportunity.risk_allowed):
        return Decision.REJECT
    if not assess(opportunity).profitable:
        return Decision.REJECT
    if not context.provider_certified or not context.external_execution_enabled:
        return Decision.SIMULATE
    return Decision.HUMAN_REQUIRED
