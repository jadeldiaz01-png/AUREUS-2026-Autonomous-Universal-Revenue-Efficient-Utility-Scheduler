from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class RevenueStage(StrEnum):
    RESEARCH = "RESEARCH"
    AUTHORIZED = "AUTHORIZED"
    ACTIVE = "ACTIVE"
    SETTLED = "SETTLED"
    SUSPENDED = "SUSPENDED"


@dataclass(frozen=True)
class RevenueChannel:
    channel_id: str
    expected_net_usd: Decimal
    probability_of_settlement: Decimal
    operational_risk: Decimal
    stage: RevenueStage
    platform_authorized: bool
    settlement_verifiable: bool

    @property
    def risk_adjusted_value(self) -> Decimal:
        return self.expected_net_usd * self.probability_of_settlement * (Decimal("1") - self.operational_risk)


@dataclass(frozen=True)
class CompoundingPolicy:
    reserve_fraction_min: Decimal = Decimal("0.50")
    reinvestment_fraction_max: Decimal = Decimal("0.25")
    experimental_fraction_max: Decimal = Decimal("0.05")

    def allocation(self, verified_net_cash_settled: Decimal) -> dict[str, Decimal]:
        if verified_net_cash_settled <= 0:
            return {"reserve": Decimal("0"), "reinvest": Decimal("0"), "experimental": Decimal("0")}
        reinvest = verified_net_cash_settled * self.reinvestment_fraction_max
        experimental = verified_net_cash_settled * self.experimental_fraction_max
        reserve = verified_net_cash_settled - reinvest - experimental
        if reserve < verified_net_cash_settled * self.reserve_fraction_min:
            raise ValueError("reserve invariant violated")
        return {"reserve": reserve, "reinvest": reinvest, "experimental": experimental}


def rank_channels(channels: list[RevenueChannel]) -> list[RevenueChannel]:
    eligible = [
        channel
        for channel in channels
        if channel.platform_authorized
        and channel.settlement_verifiable
        and channel.stage in {RevenueStage.AUTHORIZED, RevenueStage.ACTIVE, RevenueStage.SETTLED}
        and channel.expected_net_usd > 0
        and Decimal("0") <= channel.probability_of_settlement <= Decimal("1")
        and Decimal("0") <= channel.operational_risk < Decimal("1")
    ]
    return sorted(eligible, key=lambda channel: channel.risk_adjusted_value, reverse=True)
